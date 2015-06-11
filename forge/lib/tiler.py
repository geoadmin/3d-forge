# -*- coding: utf-8 -*-

import os
import time
import datetime
import subprocess
import osgeo.ogr as ogr
import osgeo.osr as osr
from boto.s3.key import Key
from forge.lib.boto_conn import getBucket
from forge.lib.helpers import isShapefile, gzippedFileContent
from forge.models.terrain import TerrainTile
from forge.lib.loaders import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology
from forge.lib.global_geodetic import GlobalGeodetic


class GlobalGeodeticTiler:

    def __init__(self, minLon, maxLon, minLat, maxLat, tileMinZ, tileMaxZ, dataSourcePaths):
        self.t0 = time.time()
        self.minLon = float(minLon)
        self.maxLon = float(maxLon)
        self.minLat = float(minLat)
        self.maxLat = float(maxLat)

        self.geodetic = GlobalGeodetic(True)

        self.tileMinZ = int(tileMinZ)
        self.tileMaxZ = int(tileMaxZ)

        # Here we excpect a list of shapefiles
        self.dataSourcePaths = self._validateDataSources(dataSourcePaths)
        self.dataSourceIndex = 0

    def createTiles(self):
        baseName = '.tmp/temp_mesh'
        extension = '.terrain'
        bucket = getBucket()
        count = 1
        for tileZ in xrange(self.tileMinZ, self.tileMaxZ + 1):
            dataSourcePath = self.dataSourcePaths[self.dataSourceIndex]
            tileMinX, tileMinY = self.geodetic.LonLatToTile(self.minLon, self.minLat, tileZ)
            tileMaxX, tileMaxY = self.geodetic.LonLatToTile(self.maxLon, self.maxLat, tileZ)

            for tileX in xrange(tileMinX, tileMaxX + 1):
                for tileY in xrange(tileMinY, tileMaxY + 1):
                    self._cleanup('%s%s' % (baseName, extension), baseName, [extension])
                    tempFileTarget = '%s%s' % (baseName, extension)

                    bounds = self.geodetic.TileBounds(tileX, tileY, tileZ)
                    clipPath = self._clip(dataSourcePath, bounds)
                    shapefile = ShpToGDALFeatures(shpFilePath=clipPath)
                    features = shapefile.__read__()
                    features = self._splitAndRemoveNonTriangles(features)
                    terrainTopo = TerrainTopology(features)
                    terrainTopo.create()
                    terrainFormat = TerrainTile()
                    terrainFormat.fromTerrainTopology(terrainTopo)
                    terrainFormat.toFile(tempFileTarget)
                    compressedContent = gzippedFileContent(tempFileTarget)
                    bucketKey = '%s/%s/%s.terrain' % (tileZ, tileX, tileY)
                    print 'Uploading %s to S3' % bucketKey
                    self.writeToS3(bucket, bucketKey, compressedContent)
                    t1 = time.time()
                    ti = t1 - self.t0
                    print 'It took %s HH:MM:SS to write %s tiles' % (str(datetime.timedelta(seconds=ti)), count)
                    count += 1

            self.dataSourceIndex += 1

    def _writeToS3(b, path, content, contentType='application/octet-stream'):
        headers = {'Content-Type': contentType}
        k = Key(b)
        k.key = path
        headers['Content-Encoding'] = 'gzip'
        k.set_contents_from_file(content, headers=headers)

    def _splitAndRemoveNonTriangles(self, features):
        baseName = '.tmp/processed_clip'
        extensions = ['.shp', '.shx', '.prj', '.dbf']
        self._cleanup('%s%s' % (baseName, extensions[0]), baseName, extensions)
        drv = ogr.GetDriverByName('ESRI Shapefile')
        dataSource = drv.CreateDataSource('%s%s' % (baseName, extensions[0]))
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        layer = dataSource.CreateLayer('%s%s' % (baseName, extensions[0]), srs, ogr.wkbPolygon25D)

        for feature in features:
            geometry = feature.GetGeometryRef()
            ring = geometry.GetGeometryRef(0)
            # Retrieves all the coordinates of the ring
            points = ring.GetPoints()
            nbPoints = len(points)
            if nbPoints == 5 or nbPoints == 6:
                triangles = self._createTrianglesFromPoints(points)
                for triangle in triangles:
                    pA = triangle[0]
                    pB = triangle[1]
                    pC = triangle[2]

                    ring = ogr.Geometry(ogr.wkbLinearRinig)
                    ring.AddPoint(pA[0], pA[1], pA[2])
                    ring.AddPoint(pB[0], pB[1], pB[2])
                    ring.AddPoint(pC[0], pC[1], pC[2])
                    ring.AddPoint(pA[0], pA[1], pA[2])
                    polygon = ogr.Geometry(ogr.wkbPolygon)
                    polygon.AddGeometry(ring)

                    feat = ogr.Feature(layer.GetLayerDefn())
                    feat.SetGeometry(polygon)
                    layer.CreateFeature(feat)
                    feat.Destroy()
            else:
                layer.CreateFeature(feature)
                feature.Destroy()
        dataSource.Destroy()
        newShapefile = ShpToGDALFeatures(shpFilePath='%s%s' % (baseName, extensions[0]))
        return newShapefile.__read__()

    def _createTrianglesFromPoints(self, points):
        coords = points[0: len(points) - 1]
        nbCoords = len(coords)
        if nbCoords != 4 or nbCoords != 5:
            raise Exception('Error while processing geometries of a clipped shapefile: %s have been found' % nbCoords)

        # TODO Create a more general algo
        if nbCoords == 4:
            return self._createTrianglesFromRectangle(coords)
        else:
            # Create all possible pairs of coordinates
            distances = []
            coordsPairA = [coords[0], coords[2]]
            coordsPairB = [coords[1], coords[3]]
            coordsPairC = [coords[2], coords[4]]
            coordsPairD = [coords[3], coords[0]]
            coordsPairE = [coords[4], coords[1]]
            distances.append(self._distanceSquared(coordsPairA[0], coordsPairA[1]))
            distances.append(self._distanceSquared(coordsPairB[0], coordsPairB[1]))
            distances.append(self._distanceSquared(coordsPairC[0], coordsPairC[1]))
            distances.append(self._distanceSquared(coordsPairD[0], coordsPairD[1]))
            distances.append(self._distanceSquared(coordsPairE[0], coordsPairE[1]))
            index = distances.index(max(distances))
            if index == 0:
                tr = coordsPairA + coords[1]
            elif index == 1:
                tr = coordsPairB + coords[2]
            elif index == 2:
                tr = coordsPairC + coords[3]
            elif index == 3:
                tr = coordsPairD + coords[4]
            elif index == 4:
                tr = coordsPairE + coords[0]

            return tr + self._createTrianglesFromRectangle(list(set(coords) - set(tr)))

    def _createTrianglesFromRectangle(self, coords):
        coordsPairA = [coords[0], coords[2]]
        coordsPairB = [coords[1], coords[3]]
        distanceSquaredA = self._distanceSquared(coordsPairA[0], coordsPairA[1])
        distanceSquaredB = self._distanceSquared(coordsPairB[0], coordsPairB[1])
        if distanceSquaredA > distanceSquaredB:
            triangle1 = coordsPairA + coords[1]
            triangle2 = coordsPairA + coords[3]
        else:
            triangle1 = coordsPairB + coords[0]
            triangle2 = coordsPairB + coords[2]
        return [triangle1, triangle2]

    def _distanceSquared(self, p1, p2):
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2

    def _clip(self, inFile, bounds):
        baseName = '.tmp/clip'
        extensions = ['.shp', '.shx', '.prj', '.dbf']
        outFile = '%s%s' % (baseName, extensions[0])

        self._cleanup(outFile, baseName, extensions)

        try:
            subprocess.call('ogr2ogr -f "ESRI Shapefile" -clipsrc %s %s %s' % (' '.join(map(str, bounds)), outFile, inFile), shell=True)
        except Exception as e:
            raise Exception('An error occured while clipping the shapefile %s' % e)
        return outFile

    def _cleanup(self, outFile, baseName, extensions):
        if os.path.isfile(outFile):
            for ext in extensions:
                os.remove('%s%s' % (baseName, ext))

    def _validateDataSources(self, paths):
        if (self.tileMaxZ - self.tileMinZ + 1) != len(paths):
            raise Exception('Invalid length for dataSourcePaths %s' % paths)

        if not isinstance(paths, list):
            raise Exception('A list of paths to shapefiles is expected')
        for path in paths:
            if not os.path.isfile(path):
                raise Exception('%s does not exists')
            if not isShapefile(path):
                raise Exception('Only shapefiles are supported. Provided path %s' % path)
        return paths
