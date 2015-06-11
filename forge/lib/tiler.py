# -*- coding: utf-8 -*-

import os
import time
import datetime
import subprocess
from forge.lib.boto_conn import getBucket, writeToS3
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
                    rings = self._splitAndRemoveNonTriangles(features)
                    terrainTopo = TerrainTopology(ringsCoordinates=rings)
                    terrainTopo.fromRingsCoordinates()
                    terrainFormat = TerrainTile()
                    terrainFormat.fromTerrainTopology(terrainTopo, bounds=bounds)
                    terrainFormat.toFile(tempFileTarget)
                    compressedContent = gzippedFileContent(tempFileTarget)
                    bucketKey = '%s/%s/%s.terrain' % (tileZ, tileX, tileY)
                    print 'Uploading %s to S3' % bucketKey
                    writeToS3(bucket, bucketKey, compressedContent)
                    t1 = time.time()
                    ti = t1 - self.t0
                    print 'It took %s HH:MM:SS to write %s tiles' % (str(datetime.timedelta(seconds=ti)), count)
                    count += 1

            self.dataSourceIndex += 1

    def _splitAndRemoveNonTriangles(self, features):
        rings = []
        for feature in features:
            geometry = feature.GetGeometryRef()
            ring = geometry.GetGeometryRef(0)
            # Retrieves all the coordinates of the ring
            points = ring.GetPoints()
            nbPoints = len(points)
            if nbPoints >= 5:
                triangles = self._createTrianglesFromPoints(points)
                rings += triangles
            else:
                rings += [points[0: len(points) - 1]]
        return rings

    def _createTrianglesFromPoints(self, points):
        # Transform tuples into lists and remove redundant coord
        def listit(t):
            return list(map(listit, t)) if isinstance(t, (list, tuple)) else t
        coords = listit(points[0: len(points) - 1])

        nbCoords = len(coords)
        if nbCoords not in (4, 5):
            raise Exception('Error while processing geometries of a clipped shapefile: %s coords have been found' % nbCoords)

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
                tr = coordsPairA + [coords[1]]
                opposedP = coords.index(coords[1])
            elif index == 1:
                tr = coordsPairB + [coords[2]]
                opposedP = coords.index(coords[2])
            elif index == 2:
                tr = coordsPairC + [coords[3]]
                opposedP = coords.index(coords[3])
            elif index == 3:
                tr = coordsPairD + [coords[4]]
                opposedP = coords.index(coords[4])
            elif index == 4:
                tr = coordsPairE + [coords[0]]
                opposedP = coords.index(coords[0])

            # Remove the converging point
            coords.pop(opposedP)

            return [tr] + self._createTrianglesFromRectangle(coords)

    def _createTrianglesFromRectangle(self, coords):
        coordsPairA = [coords[0], coords[2]]
        coordsPairB = [coords[1], coords[3]]
        distanceSquaredA = self._distanceSquared(coordsPairA[0], coordsPairA[1])
        distanceSquaredB = self._distanceSquared(coordsPairB[0], coordsPairB[1])
        if distanceSquaredA > distanceSquaredB:
            triangle1 = coordsPairA + [coords[1]]
            triangle2 = coordsPairA + [coords[3]]
        else:
            triangle1 = coordsPairB + [coords[0]]
            triangle2 = coordsPairB + [coords[2]]
        return [triangle1, triangle2]

    def _distanceSquared(self, p1, p2):
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2

    def _clip(self, inFile, bounds):
        baseName = '.tmp/clip'
        extensions = ['.shp', '.shx', '.prj', '.dbf']
        outFile = '%s%s' % (baseName, extensions[0])

        self._cleanup(outFile, baseName, extensions)

        t0 = time.time()
        print 'Clipping tile...'
        try:
            subprocess.call('ogr2ogr -f "ESRI Shapefile" -clipsrc %s %s %s' % (' '.join(map(str, bounds)), outFile, inFile), shell=True)
        except Exception as e:
            raise Exception('An error occured while clipping the shapefile %s' % e)
        t1 = time.time()
        ti = t1 - t0
        print 'It took %s HH:MM:SS to clip the tile.' % str(datetime.timedelta(seconds=ti))
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
