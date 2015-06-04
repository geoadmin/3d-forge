# -*- coding: utf-8 -*-

import os
import osgeo.ogr as ogr
import osgeo.osr as osr
from collections import OrderedDict
from forge.lib.topology import TerrainTopology
from forge.lib.bounding_sphere import BoundingSphere
from forge.lib.helpers import zigZagDecode, zigZagEncode, transformCoordinate
from forge.lib.llh_ecef import LLH2ECEF
from forge.lib.decoders import unpackEntry, unpackIndices, decodeIndices, packEntry, packIndices, encodeIndices

MAX = 32767.0


def lerp(p, q, time):
    return ((1.0 - time) * p) + (time * q)

# http://cesiumjs.org/data-and-assets/terrain/formats/quantized-mesh-1.0.html


class TerrainTile:
    quantizedMeshHeader = OrderedDict([
        ['centerX', 'd'],  # 8bytes
        ['centerY', 'd'],
        ['centerZ', 'd'],
        ['minimumHeight', 'f'],  # 4bytes
        ['maximumHeight', 'f'],
        ['boundingSphereCenterX', 'd'],
        ['boundingSphereCenterY', 'd'],
        ['boundingSphereCenterZ', 'd'],
        ['boundingSphereRadius', 'd'],
        ['horizonOcclusionPointX', 'd'],
        ['horizonOcclusionPointY', 'd'],
        ['horizonOcclusionPointZ', 'd']
    ])

    vertexData = OrderedDict([
        ['vertexCount', 'I'],  # 4bytes -> determines the size of the 3 following arrays
        ['uVertexCount', 'H'],  # 2bytes, unsigned short
        ['vVertexCount', 'H'],
        ['heightVertexCount', 'H']
    ])

    indexData16 = OrderedDict([
        ['triangleCount', 'I'],
        ['indices', 'H']
    ])
    indexData32 = OrderedDict([
        ['triangleCount', 'I'],
        ['indices', 'I']
    ])

    EdgeIndices16 = OrderedDict([
        ['westVertexCount', 'I'],
        ['westIndices', 'H'],
        ['southVertexCount', 'I'],
        ['southIndices', 'H'],
        ['eastVertexCount', 'I'],
        ['eastIndices', 'H'],
        ['northVertexCount', 'I'],
        ['northIndices', 'H']
    ])

    EdgeIndices32 = OrderedDict([
        ['westVertexCount', 'I'],
        ['westIndices', 'I'],
        ['southVertexCount', 'I'],
        ['southIndices', 'I'],
        ['eastVertexCount', 'I'],
        ['eastIndices', 'I'],
        ['northVertexCount', 'I'],
        ['northIndices', 'I']
    ])

    BYTESPLIT = 65636

    # Coordinates are given in lon/lat WSG84
    def __init__(self, west=None, east=None, south=None, north=None):
        self._west = west if west is not None else -1.0
        self._east = east if east is not None else 1.0
        self._south = south if south is not None else -1.0
        self._north = north if north is not None else 1.0
        self._longs = []
        self._lats = []
        self._heights = []
        # Reprojected coordinates
        self._easts = []
        self._norths = []
        self._alts = []
        self.targetEPSG = 4326

        self.header = OrderedDict()
        for k, v in TerrainTile.quantizedMeshHeader.iteritems():
            self.header[k] = 0.0
        self.u = []
        self.v = []
        self.h = []
        self.indices = []
        self.westI = []
        self.southI = []
        self.eastI = []
        self.northI = []

    def __str__(self):

        str = 'Header: %s' % self.header
        str += '\nVertexCount: %s' % len(self.u)
        str += '\nuVertex: %s' % self.u
        str += '\nvVertex: %s' % self.v
        str += '\nhVertex: %s' % self.h
        str += '\nindexDataCount: %s' % len(self.indices)
        str += '\nindexData: %s' % self.indices
        str += '\nwestIndicesCount: %s' % len(self.westI)
        str += '\nwestIndices: %s' % self.westI
        str += '\nsouthIndicesCount: %s' % len(self.southI)
        str += '\nsouthIndices: %s' % self.southI
        str += '\neastIndicesCount: %s' % len(self.eastI)
        str += '\neastIndices: %s' % self.eastI
        str += '\nnorthIndicesCount: %s' % len(self.northI)
        str += '\nnorthIndices: %s' % self.northI
        # output coordinates
        str += '\nCoordinates in EPSG %s ----------------------------\n' % self.targetEPSG
        str += '\n%s' % self.getVerticesCoordinates(epsg=self.targetEPSG)

        str += '\nNumber of triangles: %s' % (len(self.indices) / 3)
        return str

    def getVerticesCoordinates(self, epsg=4326):
        coordinates = []
        if epsg == 4326:
            if len(self._longs) == 0:
                self.computeVerticesCoordinates()
            for i, lon in enumerate(self._longs):
                coordinates.append([lon, self._lats[i], self._heights[i]])
        elif epsg != 4326:
            if len(self._easts) == 0:
                self.computeVerticesCoordinates(epsg=epsg)
            for i, east in enumerate(self._easts):
                coordinates.append([east, self._norths[i], self._alts[i]])
        return coordinates

    # This is really slow, so only do it when really needed
    def computeVerticesCoordinates(self, epsg=4326):
        if len(self._longs) == 0:
            for u in self.u:
                self._longs.append(lerp(self._west, self._east, float(u) / MAX))
            for v in self.v:
                self._lats.append(lerp(self._south, self._north, float(v) / MAX))
            for h in self.h:
                self._heights.append(lerp(self.header['minimumHeight'], self.header['maximumHeight'], float(h) / MAX))

        if epsg != 4326:
            self._reprojectVerticesCoordinates(epsg)

    def _resetReprojectedVerticesCoordinates(self):
        self._easts = []
        self._norths = []
        self._alts = []

    def _reprojectVerticesCoordinates(self, epsg):
        if self.targetEPSG != epsg:
            self._resetReprojectedVerticesCoordinates()
        if len(self._easts) == 0:
            self.targetEPSG = epsg
            for i, lon in enumerate(self._longs):
                lat = self._lats[i]
                height = self._heights[i]
                point = 'POINT (%f %f %f)' % (lon, lat, height)
                p = transformCoordinate(point, 4326, epsg)
                self._easts.append(p.GetX())
                self._norths.append(p.GetY())
                self._alts.append(p.GetZ())

    def fromFile(self, filePath, west, east, south, north):
        self.__init__(west, east, south, north)
        with open(filePath, 'rb') as f:
            # Header
            for k, v in TerrainTile.quantizedMeshHeader.iteritems():
                self.header[k] = unpackEntry(f, v)

            # Delta decoding
            ud = 0
            vd = 0
            hd = 0
            # Vertices
            vertexCount = unpackEntry(f, TerrainTile.vertexData['vertexCount'])
            for i in range(0, vertexCount):
                ud += zigZagDecode(unpackEntry(f, TerrainTile.vertexData['uVertexCount']))
                self.u.append(ud)
            for i in range(0, vertexCount):
                vd += zigZagDecode(unpackEntry(f, TerrainTile.vertexData['vVertexCount']))
                self.v.append(vd)
            for i in range(0, vertexCount):
                hd += zigZagDecode(unpackEntry(f, TerrainTile.vertexData['heightVertexCount']))
                self.h.append(hd)

            # Indices
            # TODO: verify padding
            meta = TerrainTile.indexData16
            if vertexCount > TerrainTile.BYTESPLIT:
                meta = TerrainTile.indexData32
            triangleCount = unpackEntry(f, meta['triangleCount'])
            ind = unpackIndices(f, triangleCount * 3, meta['indices'])
            self.indices = decodeIndices(ind)

            meta = TerrainTile.EdgeIndices16
            if vertexCount > TerrainTile.BYTESPLIT:
                meta = TerrainTile.indexData32
            # Edges (vertices on the edge of the tile) indices (are the also high water mark encoded?)
            westIndicesCount = unpackEntry(f, meta['westVertexCount'])
            self.westI = unpackIndices(f, westIndicesCount, meta['westIndices'])

            southIndicesCount = unpackEntry(f, meta['southVertexCount'])
            self.southI = unpackIndices(f, southIndicesCount, meta['southIndices'])

            eastIndicesCount = unpackEntry(f, meta['eastVertexCount'])
            self.eastI = unpackIndices(f, eastIndicesCount, meta['eastIndices'])

            northIndicesCount = unpackEntry(f, meta['northVertexCount'])
            self.northI = unpackIndices(f, northIndicesCount, meta['northIndices'])

            data = f.read(1)
            if data:
                raise Exception('Should have reached end of file, but didn\'t')

    def toFile(self, filePath):
        if not filePath.endswith('.terrain'):
            raise Exception('Wrong file extension')

        if os.path.isfile(filePath):
            raise IOError('File %s already exists' % filePath)

        with open(filePath, 'wb') as f:
            # Header
            for k, v in TerrainTile.quantizedMeshHeader.iteritems():
                f.write(packEntry(v, self.header[k]))

            # Delta decoding
            vertexCount = len(self.u)
            # Vertices
            f.write(packEntry(TerrainTile.vertexData['vertexCount'], vertexCount))
            # Move the initial value
            f.write(packEntry(TerrainTile.vertexData['uVertexCount'], zigZagEncode(self.u[0])))
            for i in range(0, vertexCount - 1):
                ud = self.u[i + 1] - self.u[i]
                f.write(packEntry(TerrainTile.vertexData['uVertexCount'], zigZagEncode(ud)))
            f.write(packEntry(TerrainTile.vertexData['uVertexCount'], zigZagEncode(self.v[0])))
            for i in range(0, vertexCount - 1):
                vd = self.v[i + 1] - self.v[i]
                f.write(packEntry(TerrainTile.vertexData['vVertexCount'], zigZagEncode(vd)))
            f.write(packEntry(TerrainTile.vertexData['uVertexCount'], zigZagEncode(self.h[0])))
            for i in range(0, vertexCount - 1):
                hd = self.h[i + 1] - self.h[i]
                f.write(packEntry(TerrainTile.vertexData['heightVertexCount'], zigZagEncode(hd)))

            # Indices
            # TODO: verify padding
            meta = TerrainTile.indexData16
            if vertexCount > TerrainTile.BYTESPLIT:
                meta = TerrainTile.indexData32

            f.write(packEntry(meta['triangleCount'], len(self.indices) / 3))
            ind = encodeIndices(self.indices)
            packIndices(f, meta['indices'], ind)

            meta = TerrainTile.EdgeIndices16
            if vertexCount > TerrainTile.BYTESPLIT:
                meta = TerrainTile.indexData32

            f.write(packEntry(meta['westVertexCount'], len(self.westI)))
            for wi in self.westI:
                f.write(packEntry(meta['westIndices'], wi))

            f.write(packEntry(meta['southVertexCount'], len(self.southI)))
            for si in self.southI:
                f.write(packEntry(meta['southIndices'], si))

            f.write(packEntry(meta['eastVertexCount'], len(self.eastI)))
            for ei in self.eastI:
                f.write(packEntry(meta['eastIndices'], ei))

            f.write(packEntry(meta['northVertexCount'], len(self.northI)))
            for ni in self.northI:
                f.write(packEntry(meta['northIndices'], ni))
        print '%s has been created successfully' % filePath

    def toShapefile(self, filePath, epsg=4326):
        if not filePath.endswith('.shp'):
            raise Exception('Wrong file extension')

        if os.path.isfile(filePath):
            raise IOError('File %s already exists' % filePath)

        if len(self.indices) == 0:
            raise Exception('No indices, you must first generate the topology')

        coords = self.getVerticesCoordinates(epsg=epsg)

        baseName = os.path.split(filePath)[1]
        drv = ogr.GetDriverByName('ESRI Shapefile')
        dataSource = drv.CreateDataSource(filePath)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        layer = dataSource.CreateLayer(baseName, srs, ogr.wkbPolygon25D)
        for i in range(0, len(self.indices), 3):
            # Indices of triangle a,b,c
            a = self.indices[i]
            b = self.indices[i + 1]
            c = self.indices[i + 2]
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(coords[a][0], coords[a][1], coords[a][2])
            ring.AddPoint(coords[b][0], coords[b][1], coords[c][2])
            ring.AddPoint(coords[c][0], coords[c][1], coords[c][2])
            ring.AddPoint(coords[a][0], coords[a][0], coords[a][2])
            polygon = ogr.Geometry(ogr.wkbPolygon)
            polygon.AddGeometry(ring)

            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetGeometry(polygon)
            layer.CreateFeature(feature)
            feature.Destroy()
        dataSource.Destroy()
        print '%s has been created successfully' % filePath

    def fromTerrainTopology(self, topology):
        if not isinstance(topology, TerrainTopology):
            raise Exception('topology object must be an instance of TerrainTopology')

        # Set tile bounds
        # TODO handle borders transitions
        self._west = topology.minLon
        self._east = topology.maxLon
        self._south = topology.minLat
        self._north = topology.maxLat

        llh2ecef = lambda x: LLH2ECEF(x[0], x[1], x[2])
        ecefCoords = map(llh2ecef, topology.coords)
        bSphere = BoundingSphere()
        bSphere.fromPoints(ecefCoords)

        ecefMinX = float('inf')
        ecefMinY = float('inf')
        ecefMinZ = float('inf')
        ecefMaxX = float('-inf')
        ecefMaxY = float('-inf')
        ecefMaxZ = float('-inf')

        for coord in ecefCoords:
            if coord[0] < ecefMinX:
                ecefMinX = coord[0]
            if coord[1] < ecefMinY:
                ecefMinY = coord[1]
            if coord[2] < ecefMinZ:
                ecefMinZ = coord[2]
            if coord[0] > ecefMaxX:
                ecefMaxX = coord[0]
            if coord[1] > ecefMaxY:
                ecefMaxY = coord[1]
            if coord[2] > ecefMaxZ:
                ecefMaxZ = coord[2]

        centerCoords = [
            ecefMinX + (ecefMaxX - ecefMinX) * 0.5,
            ecefMinY + (ecefMaxY - ecefMinY) * 0.5,
            ecefMinZ + (ecefMaxZ - ecefMinZ) * 0.5
        ]
        # TODO just for now
        occlusionPCoords = [0.0, 0.0, 0.0]
        for k, v in TerrainTile.quantizedMeshHeader.iteritems():
            if k == 'centerX':
                self.header[k] = centerCoords[0]
            elif k == 'centerY':
                self.header[k] = centerCoords[1]
            elif k == 'centerZ':
                self.header[k] = centerCoords[2]
            elif k == 'minimumHeight':
                self.header[k] = topology.minHeight
            elif k == 'maximumHeight':
                self.header[k] = topology.maxHeight
            elif k == 'boundingSphereCenterX':
                self.header[k] = bSphere.center[0]
            elif k == 'boundingSphereCenterY':
                self.header[k] = bSphere.center[1]
            elif k == 'boundingSphereCenterZ':
                self.header[k] = bSphere.center[2]
            elif k == 'boundingSphereRadius':
                self.header[k] = bSphere.radius
            elif k == 'horizonOcclusionPointX':
                self.header[k] = occlusionPCoords[0]
            elif k == 'horizonOcclusionPointY':
                self.header[k] = occlusionPCoords[1]
            elif k == 'horizonOcclusionPointZ':
                self.header[k] = occlusionPCoords[2]

        bLon = MAX / (self._east - self._west)
        bLat = MAX / (self._north - self._south)
        bHeight = MAX / (self.header['maximumHeight'] - self.header['minimumHeight'])
        quantizeLonIndices = lambda x: int(round((x - self._west) * bLon))
        quantizeLatIndices = lambda x: int(round((x - self._south) * bLat))
        quantizeHeightIndices = lambda x: int(round((x - self.header['minimumHeight']) * bHeight))

        # High watermark encoding performed during toFile
        self.u = map(quantizeLonIndices, topology.uVertex)
        self.v = map(quantizeLatIndices, topology.vVertex)
        self.h = map(quantizeHeightIndices, topology.hVertex)
        self.indices = topology.indexData

        # List all the vertices on the edge of the tile
        # High water mark encoded?
        for i in range(0, len(self.indices)):
            # Use original coordinates
            indice = self.indices[i]
            lon = topology.uVertex[indice]
            lat = topology.vVertex[indice]

            if lon == self._west and indice not in self.westI:
                self.westI.append(indice)
            elif lon == self._east and indice not in self.eastI:
                self.eastI.append(indice)

            if lat == self._south and indice not in self.southI:
                self.southI.append(indice)
            elif lat == self._north and indice not in self.northI:
                self.northI.append(indice)
