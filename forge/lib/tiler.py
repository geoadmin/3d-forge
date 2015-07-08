# -*- coding: utf-8 -*-

import time
import datetime
import ConfigParser
from sqlalchemy.orm import scoped_session, sessionmaker
from geoalchemy2.shape import to_shape

from forge import DB
import forge.lib.cartesian2d as c2d
import forge.lib.cartesian3d as c3d
from forge.models.terrain import TerrainTile
from forge.models.tables import models
from forge.lib.boto_conn import getBucket, writeToS3
from forge.lib.helpers import gzipFileObject, timestamp, transformCoordinate
from forge.lib.topology import TerrainTopology
from forge.lib.global_geodetic import GlobalGeodetic
from forge.lib.collapse_geom import processRingsCoordinates
from forge.lib.logs import getLogger


def grid(bounds, zoomLevels):
    geodetic = GlobalGeodetic(True)

    for tileZ in zoomLevels:
        tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], tileZ)
        tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], tileZ)
        for tileX in xrange(tileMinX, tileMaxX + 1):
            for tileY in xrange(tileMinY, tileMaxY + 1):
                yield (geodetic.TileBounds(tileX, tileY, tileZ), (tileX, tileY, tileZ))


class TilerManager:

    def __init__(self, configFile):
        self.t0 = time.time()
        config = ConfigParser.RawConfigParser()
        config.read(configFile)

        self.minLon = float(config.get('Extent', 'minLon'))
        self.maxLon = float(config.get('Extent', 'maxLon'))
        self.minLat = float(config.get('Extent', 'minLat'))
        self.maxLat = float(config.get('Extent', 'maxLat'))
        self.tileMinZ = int(config.get('Zooms', 'tileMinZ'))
        self.tileMaxZ = int(config.get('Zooms', 'tileMaxZ'))

        # Perpare models
        self.models = {}
        for i in range(self.tileMinZ, self.tileMaxZ + 1):
            for model in models:
                if model.__tablename__ == config.get(str(i), 'tablename'):
                    self.models[str(i)] = model
                    break

        # DB session
        db = DB('database.cfg')
        self.DBSession = scoped_session(sessionmaker(bind=db.userEngine))

        # Init logging
        config = ConfigParser.RawConfigParser()
        config.read('database.cfg')
        self.logger = getLogger(config, __name__, suffix=timestamp())

    def create(self):
        bucket = getBucket()
        # Keep of the overall number of tiles that have been created
        count = 1

        for bounds, tileXYZ in grid((self.minLon, self.minLat, self.maxLon, self.maxLat), range(self.tileMinZ, self.tileMaxZ + 1)):
            model = self.models[str(tileXYZ[2])]
            clippedGeometry = model.bboxClippedGeom(bounds)
            query = self.DBSession.query(clippedGeometry)
            query = query.filter(model.bboxIntersects(bounds))
            ringsCoordinates = [list(to_shape(q[0]).exterior.coords) for q in query]

            bucketKey = '%s/%s/%s.terrain' % (tileXYZ[2], tileXYZ[0], tileXYZ[1])
            # Skip empty tiles for now, we should instead write an empty tile to S3
            if len(ringsCoordinates) > 0:
                try:
                    rings = processRingsCoordinates(ringsCoordinates)
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
                # One should write an empyt tile
                self.logger.info('Skipping %s because no features have been found for this tile' % bucketKey)

    def stats(self):
        msg = '\n'
        geodetic = GlobalGeodetic(True)
        bounds = (self.minLon, self.minLat, self.maxLon, self.maxLat)
        zooms = range(self.tileMinZ, self.tileMaxZ + 1)

        for i in xrange(0, len(zooms)):
            zoom = zooms[i]
            model = self.models[str(zoom)]
            nbObjects = self.DBSession.query(model).filter(model.bboxIntersects(bounds)).count()
            tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], zoom)
            tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], zoom)
            xCount = tileMaxX - tileMinX
            yCount = tileMaxY - tileMinY
            nbTiles = xCount * yCount
            tileBounds = geodetic.TileBounds(tileMinX, tileMinY, zoom)
            pointA = transformCoordinate('POINT(%s %s)' % (tileBounds[0], tileBounds[1]), 4326, 21781).GetPoints()[0]
            pointB = transformCoordinate('POINT(%s %s)' % (tileBounds[2], tileBounds[3]), 4326, 21781).GetPoints()[0]
            length = c2d.distance(pointA, pointB)
            msg += 'At zoom %s:\n' % zoom
            msg += 'We expect %s tiles overall\n' % nbTiles
            msg += 'Min X is %s, Max X is %s\n' % (tileMinX, tileMaxX)
            msg += '%s columns over X\n' % xCount
            msg += 'Min Y is %s, Max Y is %s\n' % (tileMinY, tileMaxY)
            msg += '%s rows over Y\n' % yCount
            msg += '\n'
            msg += 'A tile side is around %s meters long\n' % int(round(length))
            msg += 'We have an average of about %s triangles per tile\n' % int(round(nbObjects / nbTiles))
            msg += '\n'

        self.logger.info(msg)
