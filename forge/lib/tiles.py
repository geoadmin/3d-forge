# -*- coding: utf-8 -*-

from forge.lib.global_geodetic import GlobalGeodetic


def isInside(tile, bounds):
    if tile[0] >= bounds[0] and tile[1] >= bounds[1] and tile[2] <= bounds[2] and tile[3] <= bounds[3]:
        return True
    return False


def grid(bounds, zoomLevels, fullonly):
    geodetic = GlobalGeodetic(True)

    for tileZ in zoomLevels:
        tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], tileZ)
        tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], tileZ)

        for tileX in xrange(tileMinX, tileMaxX + 1):
            for tileY in xrange(tileMinY, tileMaxY + 1):
                tilebounds = geodetic.TileBounds(tileX, tileY, tileZ)
                if fullonly == 0 or isInside(tilebounds, bounds):
                    yield (tilebounds, (tileX, tileY, tileZ))


class Tiles:

    def __init__(self, bounds, minZoom, maxZoom, t0, fullonly=False):
        self.t0 = t0
        self.bounds = bounds
        self.tileMinZ = minZoom
        self.tileMaxZ = maxZoom
        self.fullonly = fullonly

    def __iter__(self):
        zRange = range(self.tileMinZ, self.tileMaxZ + 1)

        for bounds, tileXYZ in grid(self.bounds, zRange, self.fullonly):
            yield (bounds, tileXYZ, self.t0)


class TerrainTiles:

    def __init__(self, dbConfigFile, tmsConfig, t0):
        self.t0 = t0

        self.minLon = tmsConfig.getfloat('Extent', 'minLon')
        self.maxLon = tmsConfig.getfloat('Extent', 'maxLon')
        self.minLat = tmsConfig.getfloat('Extent', 'minLat')
        self.maxLat = tmsConfig.getfloat('Extent', 'maxLat')
        self.fullonly = tmsConfig.getint('Extent', 'fullonly')
        self.bounds = (self.minLon, self.minLat, self.maxLon, self.maxLat)

        self.bucketBasePath = tmsConfig.get('General', 'bucketpath')

        self.tileMinZ = tmsConfig.getint('Zooms', 'tileMinZ')
        self.tileMaxZ = tmsConfig.getint('Zooms', 'tileMaxZ')

        self.hasLighting = tmsConfig.getint('Extensions', 'lighting')
        self.hasWatermask = tmsConfig.getint('Extensions', 'watermask')

        self.dbConfigFile = dbConfigFile

    def __iter__(self):
        zRange = range(self.tileMinZ, self.tileMaxZ + 1)

        for bounds, tileXYZ in grid(self.bounds, zRange, self.fullonly):
            yield (bounds, tileXYZ, self.t0, self.dbConfigFile,
                self.bucketBasePath, self.hasLighting, self.hasWatermask)


class QueueTerrainTiles:

    def __init__(self, qName, dbConfigFile, tmsConfig, t0, num):
        self.t0 = t0
        self.dbConfigFile = dbConfigFile
        self.qName = qName
        self.num = num

        self.bucketBasePath = tmsConfig.get('General', 'bucketPath')

        self.hasLighting = tmsConfig.getint('Extensions', 'lighting')
        self.hasWatermask = tmsConfig.getint('Extensions', 'watermask')

    def __iter__(self):
        for i in range(0, self.num):
            yield (self.qName, self.t0, self.dbConfigFile,
                self.bucketBasePath, self.hasLighting, self.hasWatermask)
