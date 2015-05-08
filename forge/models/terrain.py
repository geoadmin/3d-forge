# -*- coding: utf-8 -*-

from collections import OrderedDict
from forge.lib.helpers import zigZagToNumber, numberToZigZag, transformCoordinate
from forge.lib.decoders import unpackEntry, unpackIndices, decodeIndices, packEntry, packIndices, encodeIndices

MAX = 32767;
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


    #Coordinates are given in lon/lat WSG84
    def __init__(self, west = None, east = None, south = None, north = None):
        self._west = west if west is not None else -1.0
        self._east = east if east is not None else 1.0
        self._south = south if south is not None else -1.0
        self._north = north if north is not None else 1.0
        self._longs = []
        self._lats = []
        self._heights = []
        # Swiss Grid coordinates
        self._easts = []
        self._norths = []

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
        def coords():
            str = '\nSwis Grid Coordinates ----------------------------\n'
            for i, east in enumerate(self._easts):
                str += '[%f, %f, %f]' % (east, self._norths[i], self._heights[i])
            return str
            

        str = 'Header: %s' % self.header
        str += '\nVertexCount: %s' % len(self.u)
        str += '\nuVertex: %s' % self.u
        str += '\nvVertex: %s' % self.v
        str += '\nhVertex: %s' % self.h
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
        str += coords()

        str += '\nNumber of triangles: %s' % (len(self.indices) / 3)
        return str


    # This is really slow, so only do it when really needed
    def _updateCoords(self):
        self._longs = []
        self._lats = []
        self._heights = []
        self._easts = []
        self._norths = []
        for u in self.u:
            self._longs.append(lerp(self._west, self._east, u / MAX))
        for v in self.v:
            self._lats.append(lerp(self._south, self._north, v / MAX))
        for h in self.h:
            self._heights.append(lerp(self.header['minimumHeight'], self.header['minimumHeight'], h / MAX))
        for i, lon in enumerate(self._longs):
            lat = self._lats[i]
            point = 'POINT (%f %f)' % (lon, lat)
            p = transformCoordinate(point, 4326, 21781)
            self._easts.append(p.GetX())
            self._norths.append(p.GetY())


    def toFile(self, filename):
        with open(filename, 'wb') as f:
            # Header
            for k, v in TerrainTile.quantizedMeshHeader.iteritems():
                f.write(packEntry(v, self.header[k]))

            # Vertices
            f.write(packEntry(TerrainTile.vertexData['vertexCount'], len(self.u)))
            for u in self.u:
                f.write(packEntry(TerrainTile.vertexData['uVertexCount'], numberToZigZag(u)))
            for v in self.v:
                f.write(packEntry(TerrainTile.vertexData['vVertexCount'], numberToZigZag(v)))
            for h in self.h:
                f.write(packEntry(TerrainTile.vertexData['heightVertexCount'], numberToZigZag(h)))

            # Indices
            # TODO: verify padding
            meta = TerrainTile.indexData16
            if len(self.u) > TerrainTile.BYTESPLIT:
                meta = TerrainTile.indexData32

            f.write(packEntry(meta['triangleCount'], len(self.indices) / 3))
            ind = encodeIndices(self.indices)
            packIndices(f, meta['indices'], ind)

            meta = TerrainTile.EdgeIndices16
            if len(self.u) > TerrainTile.BYTESPLIT:
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


    def fromFile(self, filename, west, east, south, north):
        self.__init__(west, east, south, north)
        with open(filename, 'rb') as f:
            # Header
            for k, v in TerrainTile.quantizedMeshHeader.iteritems():
                self.header[k] = unpackEntry(f, v)

            # Vertices
            vertexCount = unpackEntry(f, TerrainTile.vertexData['vertexCount'])
            for i in range(0, vertexCount):
                self.u.append(zigZagToNumber(
                    unpackEntry(f, TerrainTile.vertexData['uVertexCount'])
                ))
            for i in range(0, vertexCount):
                self.v.append(zigZagToNumber(
                    unpackEntry(f, TerrainTile.vertexData['vVertexCount'])
                ))
            for i in range(0, vertexCount):
                self.h.append(zigZagToNumber(
                    unpackEntry(f, TerrainTile.vertexData['heightVertexCount'])
                ))

            # Indices
            # TODO: verify padding
            meta = TerrainTile.indexData16
            if vertexCount > TerrainTile.BYTESPLIT:
                meta = TerrainTile.indexData32
            triangleCount = unpackEntry(f, meta['triangleCount'])
            ind = unpackIndices(f, triangleCount * 3, meta['indices'])
            self.indices = decodeIndices(ind)

            meta = TerrainTile.EdgeIndices16
            if len(self.u) > TerrainTile.BYTESPLIT:
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
