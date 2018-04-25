# -*- coding: utf-8 -*-

from gatilegrid import getTileGrid


def grid(bounds, minZ, maxZ):
    geodetic = getTileGrid(4326)(extent=bounds, tmsCompatible=True)
    gridGenerator = geodetic.iterGrid(
        minZ,
        maxZ)
    for tileBounds, tileZ, tileX, tileY in gridGenerator:
        yield (tileBounds, (tileX, tileY, tileZ))


class Tiles:

    def __init__(self, bounds, minZoom, maxZoom, t0,
                 basePath=None, tFormat=None, gridOrigin=None, tilesURLs=None):
        self.t0 = t0
        self.bounds = bounds
        self.tileMinZ = minZoom
        self.tileMaxZ = maxZoom
        self.basePath = basePath
        self.tFormat = tFormat
        self.gridOrigin = gridOrigin
        self.tilesURLs = tilesURLs

    def __iter__(self):

        for bounds, tileXYZ in grid(self.bounds, self.tileMinZ, self.tileMaxZ):
            if self.basePath and self.tFormat:
                yield (
                    bounds, tileXYZ, self.t0, self.basePath,
                    self.tFormat, self.gridOrigin, self.tilesURLs
                )
            else:
                yield (bounds, tileXYZ, self.t0)


class TerrainTiles:

    def __init__(self, dbConfigFile, tmsConfig, t0):
        self.t0 = t0

        self.minLon = tmsConfig.getfloat('Extent', 'minLon')
        self.maxLon = tmsConfig.getfloat('Extent', 'maxLon')
        self.minLat = tmsConfig.getfloat('Extent', 'minLat')
        self.maxLat = tmsConfig.getfloat('Extent', 'maxLat')
        self.bounds = (self.minLon, self.minLat, self.maxLon, self.maxLat)

        self.bucketBasePath = tmsConfig.get('General', 'bucketpath')

        self.tileMinZ = tmsConfig.getint('Zooms', 'tileMinZ')
        self.tileMaxZ = tmsConfig.getint('Zooms', 'tileMaxZ')

        self.hasLighting = tmsConfig.getint('Extensions', 'lighting')
        self.hasWatermask = tmsConfig.getint('Extensions', 'watermask')

        self.dbConfigFile = dbConfigFile

    def __iter__(self):
        for bounds, tileXYZ in grid(self.bounds, self.tileMinZ, self.tileMaxZ):
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
