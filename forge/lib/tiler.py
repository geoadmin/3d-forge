# -*- coding: utf-8 -*-

import time
import datetime
import ConfigParser
import multiprocessing
import signal
import sys
import os
import traceback
from sqlalchemy.orm import scoped_session, sessionmaker
from geoalchemy2.shape import to_shape

from forge import DB
import forge.lib.cartesian2d as c2d
from forge.models.terrain import TerrainTile
from forge.models.tables import models
from forge.lib.boto_conn import getBucket, writeToS3
from forge.lib.helpers import gzipFileObject, timestamp, transformCoordinate
from forge.lib.topology import TerrainTopology
from forge.lib.global_geodetic import GlobalGeodetic
from forge.lib.collapse_geom import processRingsCoordinates
from forge.lib.logs import getLogger

NUMBER_POOL_PROCESSES = multiprocessing.cpu_count()
# Init logging
config = ConfigParser.RawConfigParser()
config.read('database.cfg')
logger = getLogger(config, __name__, suffix=timestamp())


def grid(bounds, zoomLevels):
    geodetic = GlobalGeodetic(True)

    for tileZ in zoomLevels:
        tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], tileZ)
        tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], tileZ)
        for tileX in xrange(tileMinX, tileMaxX + 1):
            for tileY in xrange(tileMinY, tileMaxY + 1):
                yield (geodetic.TileBounds(tileX, tileY, tileZ), (tileX, tileY, tileZ))

# shared counter
tilecount = multiprocessing.Value('i', 0)
# per process counter
count = 0


# Worker processes won't recieve KeyboradInterrupts. It's parents
# responsibility to handle those (mainly Ctlr-C)
def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def take(X, Y, Z):
    if X == 17101 and Y == 12444:
        return True
    if X == 17102 and Y == 12443:
        return True
    return False;

def worker(job):
    global count
    session = None
    pid = os.getpid()
    retval = 0

    try:
        (config, tileMinZ, tileMaxZ, bounds, tileXYZ, t0, bucket) = job

        # Prepare models
        loc_models = {}
        for i in range(tileMinZ, tileMaxZ + 1):
            for model in models:
                if model.__tablename__ == config.get(str(i), 'tablename'):
                    loc_models[str(i)] = model
                    break

        if not take(tileXYZ[0], tileXYZ[1], tileXYZ[2]):
            return retval
 
        margin = 0.00000000001
        bounds = (7.88818359375 - margin, 46.7138671875 - margin, 7.88818359375, 46.7138671875)
        if tileXYZ[0] == 17101:
            bounds = (7.88818359375, 46.7138671875, 7.88818359375 + margin, 46.7138671875 + margin)
 
        db = DB('database.cfg')
        session = sessionmaker()(bind=db.userEngine)

        model = loc_models[str(tileXYZ[2])]
        clippedGeometry = model.bboxClippedGeom(bounds)

        

        query = session.query(clippedGeometry)
        query = query.filter(model.bboxIntersects(bounds))
        print query
        ringsCoordinates = [list(to_shape(q[0]).exterior.coords) for q in query]

        print ringsCoordinates
        
        return retval

        bucketKey = '%s/%s/%s.terrain' % (tileXYZ[2], tileXYZ[0], tileXYZ[1])
        # Skip empty tiles for now, we should instead write an empty tile to S3
        if len(ringsCoordinates) > 0:
            try:
                rings = processRingsCoordinates(ringsCoordinates)
            except Exception as e:
                msg = '[%s] --------- ERROR ------- occured while collapsing non triangular shapes\n'
                msg += '%s' % (pid, e)
                logger.error(msg)
                session.close_all()
                db.userEngine.dispose()
                retval = 1

            # Prepare terrain tile
            terrainTopo = TerrainTopology(ringsCoordinates=rings)
            terrainTopo.fromRingsCoordinates()
            terrainFormat = TerrainTile()
            terrainFormat.fromTerrainTopology(terrainTopo, bounds=bounds)

            # Bytes manipulation and compression
            fileObject = terrainFormat.toStringIO()
            compressedFile = gzipFileObject(fileObject)

            writeToS3(bucket, bucketKey, compressedFile)
            tend = time.time()
            tilecount.value += 1
            count += 1

            val = tilecount.value
            if val % 1 == 0:
                logger.info('The last tile address written is S3 was %s.' % bucketKey)
                logger.info('[%s] It took %s to create %s tiles on S3.' % (pid, str(datetime.timedelta(seconds=tend - t0)), val))

        else:
            # One should write an empyt tile
            logger.info('[%s] Skipping %s because no features have been found for this tile' % (pid, bucketKey))

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.debug("*** Traceback:/n" + traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
        logger.debug("*** Exception:/n" + traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))
        retval = 2

    finally:
        if session is not None:
            session.close_all()
            db.userEngine.dispose()

    return retval


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
        self.multiProcessing = int(config.get('General', 'multiProcessing'))
        self.config = config

        # Prepare models
        self.models = {}
        for i in range(self.tileMinZ, self.tileMaxZ + 1):
            for model in models:
                if model.__tablename__ == config.get(str(i), 'tablename'):
                    self.models[str(i)] = model
                    break

    def __iter__(self):
        return self.jobs()

    def jobs(self):
        bucket = getBucket()
        for bounds, tileXYZ in grid((self.minLon, self.minLat, self.maxLon, self.maxLat), range(self.tileMinZ, self.tileMaxZ + 1)):
            yield (self.config, self.tileMinZ, self.tileMaxZ, bounds, tileXYZ, self.t0, bucket)

    def create(self):
        tstart = time.time()

        if self.multiProcessing > 0:
            pool = multiprocessing.Pool(NUMBER_POOL_PROCESSES, init_worker)
            # Async needed to catch keyboard interrupt
            async = pool.map_async(worker, self)
            close = True
            try:
                while not async.ready():
                    time.sleep(3)
            except KeyboardInterrupt:
                close = False
                pool.terminate()
                logger.info('Keyboard interupt recieved')

            if close:
                pool.close()

            try:
                pool.join()
                pool.terminate()
            except Exception as e:
                for i in reversed(range(len(pool._pool))):
                    p = pool._pool[i]
                    if p.exitcode is None:
                        p.terminate()
                    del pool._pool[i]
                logger.error('Error while tiles: %s', e)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                logger.debug("*** Traceback:/n" + traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
                logger.debug("*** Exception:/n" + traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))
                return 1

        else:
            for j in self.jobs():
                worker(j)
        tend = time.time()
        logger.info('It took %s create all the tiles' % str(datetime.timedelta(seconds=tend - tstart)))

    def stats(self):
        msg = '\n'
        geodetic = GlobalGeodetic(True)
        bounds = (self.minLon, self.minLat, self.maxLon, self.maxLat)
        zooms = range(self.tileMinZ, self.tileMaxZ + 1)

        db = DB('database.cfg')
        self.DBSession = scoped_session(sessionmaker(bind=db.userEngine))

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

        logger.info(msg)
