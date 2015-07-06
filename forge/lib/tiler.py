# -*- coding: utf-8 -*-

import os
import time
import datetime
import subprocess
import ConfigParser
from forge.lib.boto_conn import getBucket, writeToS3
from forge.lib.helpers import isShapefile, gzipFileObject, timestamp
from forge.models.terrain import TerrainTile
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology
from forge.lib.global_geodetic import GlobalGeodetic
from forge.lib.logs import getLogger


def distanceSquared(p1, p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2


def grid(bounds, zoomLevels):
    geodetic = GlobalGeodetic(True)

    for tileZ in zoomLevels:
        tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], tileZ)
        tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], tileZ)
        for tileX in xrange(tileMinX, tileMaxX + 1):
            for tileY in xrange(tileMinY, tileMaxY + 1):
                yield (geodetic.TileBounds(tileX, tileY, tileZ), (tileX, tileY, tileZ))


class GlobalGeodeticTiler:

    def __init__(self, minLon, maxLon, minLat, maxLat, tileMinZ, tileMaxZ, dataSourcePaths):
        self.t0 = time.time()
        self.minLon = float(minLon)
        self.maxLon = float(maxLon)
        self.minLat = float(minLat)
        self.maxLat = float(maxLat)

        self.tileMinZ = int(tileMinZ)
        self.tileMaxZ = int(tileMaxZ)

        # Init logging
        config = ConfigParser.RawConfigParser()
        config.read('database.cfg')
        self.logger = getLogger(config, __name__, suffix=timestamp())

        # Here we excpect a list of shapefiles
        self.dataSourcePaths = self._validateDataSources(dataSourcePaths)
        self.dataSourceIndex = 0

    def createTiles(self):
        bucket = getBucket()
        count = 1
        previousTileZ = self.tileMinZ
        dataSourcePath = self.dataSourcePaths[self.dataSourceIndex]

        for bounds, tileXYZ in grid((self.minLon, self.minLat, self.maxLon, self.maxLat), range(self.tileMinZ, self.tileMaxZ + 1)):
            # Handle file index
            if tileXYZ[2] != previousTileZ:
                previousTileZ = tileXYZ[2]
                self.dataSourceIndex += 1
                dataSourcePath = self.dataSourcePaths[self.dataSourceIndex]

            # Prepare geoms
            clipPath = self._clip(dataSourcePath, bounds)
            shapefile = ShpToGDALFeatures(shpFilePath=clipPath)
            features = shapefile.__read__()

            bucketKey = '%s/%s/%s.terrain' % (tileXYZ[2], tileXYZ[0], tileXYZ[1])
            # Skip empty tiles for now, we should instead write an empty tile to S3
            if len(features) > 0:
                try:
                    rings = self._splitAndRemoveNonTriangles(features)
                except Exception as e:
                    msg = 'An error occured while collapsing non triangular shapes\n'
                    msg += '%s' % e
                    self.logger.error(msg)

                # Prepare terrain tile
                terrainTopo = TerrainTopology(ringsCoordinates=rings)
                self.logger.info('Building topology for %s rings' % len(rings))
                terrainTopo.fromRingsCoordinates()
                self.logger.info('Terrain topology has been created')
                terrainFormat = TerrainTile()
                self.logger.info('Creating terrain tile')
                terrainFormat.fromTerrainTopology(terrainTopo, bounds=bounds)
                self.logger.info('Terrain tile has been created')

                # Bytes manipulation and compression
                fileObject = terrainFormat.toStringIO()
                compressedFile = gzipFileObject(fileObject)

                self.logger.info('Uploading %s to S3' % bucketKey)
                writeToS3(bucket, bucketKey, compressedFile)
                t1 = time.time()
                ti = t1 - self.t0
                self.logger.info('It took %s HH:MM:SS to write %s tiles' % (str(datetime.timedelta(seconds=ti)), count))
                count += 1
            else:
                self.logger.info('Skipping %s because no features have been found for this tile' % bucketKey)

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
        def listit(t):
            return list(map(listit, t)) if isinstance(t, (list, tuple)) else t

        def getCoordsIndex(n, i):
            return i + 1 if n - 1 != i else 0

        # Creates all the potential pairs of coords
        def createCoordsPairs(l):
            coordsPairs = []
            for i in xrange(0, len(l)):
                coordsPairs.append([l[i], l[(i + 2) % len(l)]])
            return coordsPairs

        def squaredDistances(coordsPairs):
            sDistances = []
            for coordsPair in coordsPairs:
                sDistances.append(distanceSquared(coordsPair[0], coordsPair[1]))
            return sDistances

        # Transform tuples into lists and remove redundant coord
        coords = listit(points[0: len(points) - 1])

        nbCoords = len(coords)
        if nbCoords not in (4, 5, 6):
            raise Exception('Error while processing geometries of a clipped shapefile: %s coords have been found' % nbCoords)

        if nbCoords == 4:
            return self._createTrianglesFromRectangle(coords)
        elif nbCoords == 5:
            # Create all possible pairs of coordinates
            coordsPairs = createCoordsPairs(coords)
            sDistances = squaredDistances(coordsPairs)

            index = sDistances.index(max(sDistances))
            j = getCoordsIndex(nbCoords, index)
            tr = coordsPairs[index] + [coords[j]]
            # Remove the converging point / not available anymore to create a triangle
            opposedP = coords.index(coords[j])
            coords.pop(opposedP)

            return [tr] + self._createTrianglesFromRectangle(coords)
        elif nbCoords == 6:
            coordsPairs = createCoordsPairs(coords)
            sDistances = squaredDistances(coordsPairs)

            index = sDistances.index(max(sDistances))
            j = getCoordsIndex(nbCoords, index)
            tr1 = coordsPairs[index] + [coords[j]]
            opposedP = coords.index(coords[j])
            coords.pop(opposedP)

            coordsPairs = createCoordsPairs(coords)
            sDistances = squaredDistances(coordsPairs)

            index = sDistances.index(max(sDistances))
            j = getCoordsIndex(len(coords), index)
            tr2 = coordsPairs[index] + [coords[j]]
            opposedP = coords.index(coords[j])
            coords.pop(opposedP)

            return [tr1] + [tr2] + self._createTrianglesFromRectangle(coords)

    def _createTrianglesFromRectangle(self, coords):
        coordsPairA = [coords[0], coords[2]]
        coordsPairB = [coords[1], coords[3]]
        distanceSquaredA = distanceSquared(coordsPairA[0], coordsPairA[1])
        distanceSquaredB = distanceSquared(coordsPairB[0], coordsPairB[1])
        if distanceSquaredA > distanceSquaredB:
            triangle1 = coordsPairA + [coords[1]]
            triangle2 = coordsPairA + [coords[3]]
        else:
            triangle1 = coordsPairB + [coords[0]]
            triangle2 = coordsPairB + [coords[2]]
        return [triangle1, triangle2]

    def _clip(self, inFile, bounds):
        baseName = '.tmp/clip'
        extensions = ['.shp', '.shx', '.prj', '.dbf']
        outFile = '%s%s' % (baseName, extensions[0])

        self._cleanup(outFile, baseName, extensions)

        t0 = time.time()
        self.logger.info('Clipping tile...')
        try:
            subprocess.call('ogr2ogr -f "ESRI Shapefile" -clipsrc %s %s %s' % (' '.join(map(str, bounds)), outFile, inFile), shell=True)
        except Exception as e:
            msg = 'An error occured while clipping the shapefile %s' % e
            self.logger.error(msg)
            raise Exception(msg)
        t1 = time.time()
        ti = t1 - t0
        self.logger.info('It took %s HH:MM:SS to clip the tile.' % str(datetime.timedelta(seconds=ti)))
        return outFile

    def _cleanup(self, outFile, baseName, extensions):
        if os.path.isfile(outFile):
            for ext in extensions:
                os.remove('%s%s' % (baseName, ext))

    def _validateDataSources(self, paths):
        if (self.tileMaxZ - self.tileMinZ + 1) != len(paths):
            msg = 'Invalid length for dataSourcePaths %s' % paths
            self.logger.error(msg)
            raise Exception(msg)

        if not isinstance(paths, list):
            msg = 'A list of paths to shapefiles is expected'
            self.logger.error(msg)
            raise Exception(msg)
        for path in paths:
            if not os.path.isfile(path):
                msg = '%s does not exists' % path
                self.logger.error(msg)
                raise Exception(msg)
            if not isShapefile(path):
                msg = 'Only shapefiles are supported. Provided path %s' % path
                self.logger.error(msg)
                raise Exception(msg)
        return paths
