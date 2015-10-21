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

    def __init__(self, dbConfigFile, tmsConfig, t0):
        self.t0 = t0

        self.minLon = float(tmsConfig.get('Extent', 'minLon'))
        self.maxLon = float(tmsConfig.get('Extent', 'maxLon'))
        self.minLat = float(tmsConfig.get('Extent', 'minLat'))
        self.maxLat = float(tmsConfig.get('Extent', 'maxLat'))
        self.fullonly = int(tmsConfig.get('Extent', 'fullonly'))
        self.bounds = (self.minLon, self.minLat, self.maxLon, self.maxLat)

        self.tileMinZ = int(tmsConfig.get('Zooms', 'tileMinZ'))
        self.tileMaxZ = int(tmsConfig.get('Zooms', 'tileMaxZ'))

        self.hasLighting = int(tmsConfig.get('Extensions', 'lighting'))
        self.hasWatermask = int(tmsConfig.get('Extensions', 'watermask'))

        self.dbConfigFile = dbConfigFile

    def __iter__(self):
        zRange = range(self.tileMinZ, self.tileMaxZ + 1)

        for bounds, tileXYZ in grid(self.bounds, zRange, self.fullonly):
            yield (bounds, tileXYZ, self.t0, self.dbConfigFile, self.hasLighting, self.hasWatermask)


class QueueTiles:

    def __init__(self, qName, dbConfigFile, tmsConfig, t0, num):
        self.t0 = t0
        self.dbConfigFile = dbConfigFile
        self.qName = qName
        self.num = num

        self.hasLighting = int(tmsConfig.get('Extensions', 'lighting'))
        self.hasWatermask = int(tmsConfig.get('Extensions', 'watermask'))

    def __iter__(self):
        for i in range(0, self.num):
            yield (self.qName, self.t0, self.dbConfigFile, self.hasLighting, self.hasWatermask)
