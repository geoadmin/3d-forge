# -*- coding: utf-8 -*-

import time
import datetime
import ConfigParser
import multiprocessing
import signal
import os
from sqlalchemy.sql import and_
from sqlalchemy.orm import scoped_session, sessionmaker
from geoalchemy2 import WKBElement
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
dbConfig = ConfigParser.RawConfigParser()
dbConfig.read('database.cfg')
logger = getLogger(dbConfig, __name__, suffix=timestamp())


def is_inside(tile, bounds):
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
                if fullonly == 0 or is_inside(tilebounds, bounds):
                    yield (tilebounds, (tileX, tileY, tileZ))

# shared counter
tilecount = multiprocessing.Value('i', 0)
skipcount = multiprocessing.Value('i', 0)
# per process counter
count = 0

# Worker processes won't recieve KeyboradInterrupts. It's parents
# responsibility to handle those (mainly Ctlr-C)


def initWorker():
    logger.info('Starting process id: %s' % multiprocessing.current_process().pid)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def prepareModelsPyramid(tileMinZ, tileMaxZ, tmsConfig):
    modelsPyramid = {}
    for i in range(tileMinZ, tileMaxZ + 1):
        for model in models:
            if model.__tablename__ == tmsConfig.get(str(i), 'tablename'):
                modelsPyramid[str(i)] = model
                break
    return modelsPyramid


def worker(job):
    global count
    session = None
    pid = os.getpid()

    try:
        (tmsConfig, tileMinZ, tileMaxZ, bounds, tileXYZ, t0, bucket) = job
        # Prepare models
        modelsPyramid = prepareModelsPyramid(tileMinZ, tileMaxZ, tmsConfig)
        db = DB('database.cfg')
        session = sessionmaker()(bind=db.userEngine)

        # Get the model according to the zoom level
        model = modelsPyramid[str(tileXYZ[2])]

        # Get the interpolated point at the 4 corners
        # 0: (minX, minY), 1: (minX, maxY), 2: (maxX, maxY), 3: (maxX, minY)
        p_0 = (bounds[0], bounds[1], 0)
        p_1 = (bounds[0], bounds[3], 0)
        p_2 = (bounds[2], bounds[3], 0)
        p_3 = (bounds[2], bounds[1], 0)
        pts = [p_0, p_1, p_2, p_3]
        cornerPts = {}

        # Get the height of the corner points as postgis cannot properly clip
        # a polygon
        for pt in pts:
            query = session.query(model.id, model.interpolateHeightOnPlane(pt, model.the_geom).label('p')).filter(
                and_(model.bboxIntersects(bounds), model.pointIntersects(pt))
            )
            for q in query:
                cornerPts[q.id] = list(to_shape(WKBElement(q.p)).coords)
        # Clip using the bounds
        clippedGeometry = model.bboxClippedGeom(bounds)
        query = session.query(
            model.id,
            clippedGeometry.label('clip')
        ).filter(model.bboxIntersects(bounds))

        ringsCoordinates = []
        for q in query:
            coords = list(to_shape(q.clip).exterior.coords)
            if q.id in cornerPts:
                pt = cornerPts[q.id][0]
                for i in range(0, len(coords)):
                    c = coords[i]
                    if c[0] == pt[0] and c[1] == pt[1]:
                        coords[i] = [c[0], c[1], pt[2]]
            ringsCoordinates.append(coords)

        bucketKey = '%s/%s/%s.terrain' % (tileXYZ[2], tileXYZ[0], tileXYZ[1])
        # Skip empty tiles for now, we should instead write an empty tile to S3
        if len(ringsCoordinates) > 0:
            try:
                rings = processRingsCoordinates(ringsCoordinates)
            except Exception as e:
                msg = '[%s] --------- ERROR ------- occured while collapsing non triangular shapes\n'
                msg += '%s' % (pid, e)
                logger.error(msg)
                raise Exception(e)

            # Prepare terrain tile
            terrainTopo = TerrainTopology(ringsCoordinates=rings)
            terrainTopo.fromRingsCoordinates()
            terrainFormat = TerrainTile()
            terrainFormat.fromTerrainTopology(terrainTopo, bounds=bounds)

            # Bytes manipulation and compression
            fileObject = terrainFormat.toStringIO()
            compressedFile = gzipFileObject(fileObject)
            writeToS3(bucket, bucketKey, compressedFile, model.__tablename__)
            tend = time.time()
            tilecount.value += 1
            count += 1
            val = tilecount.value
            total = val + skipcount.value
            if val % 10 == 0:
                logger.info('The last tile address written in S3 was %s, and contained %s rings.' % (bucketKey, len(rings)))
                logger.info('[%s] It took %s to create %s tiles on S3. (total processed: %s)' % (pid, str(datetime.timedelta(seconds=tend - t0)), val, total))

        else:
            skipcount.value += 1
            val = skipcount.value
            total = val + tilecount.value
            # One should write an empyt tile
            logger.info('[%s] Skipping %s because no features found for this tile (%s skipped from %s total)' % (pid, bucketKey, val, total))

    except Exception as e:
        raise Exception(e)
    finally:
        if session is not None:
            session.close_all()
            db.userEngine.dispose()

    return 0


class Jobs:

    def __init__(self, tmsConfig, t0):
        self.t0 = t0

        self.minLon = float(tmsConfig.get('Extent', 'minLon'))
        self.maxLon = float(tmsConfig.get('Extent', 'maxLon'))
        self.minLat = float(tmsConfig.get('Extent', 'minLat'))
        self.maxLat = float(tmsConfig.get('Extent', 'maxLat'))
        self.fullonly = int(tmsConfig.get('Extent', 'fullonly'))

        self.tileMinZ = int(tmsConfig.get('Zooms', 'tileMinZ'))
        self.tileMaxZ = int(tmsConfig.get('Zooms', 'tileMaxZ'))

        self.tmsConfig = tmsConfig

    def __iter__(self):
        bucket = getBucket()
        zRange = range(self.tileMinZ, self.tileMaxZ + 1)
        for bounds, tileXYZ in grid((self.minLon, self.minLat, self.maxLon, self.maxLat), zRange, self.fullonly):
            yield (self.tmsConfig, self.tileMinZ, self.tileMaxZ, bounds, tileXYZ, self.t0, bucket)


class Chunks:

    def __init__(self, jobs):
        self.itr = iter(jobs)

    def nextX(self, N):
        res = []
        count = 0
        try:
            while count < N:
                n = self.itr.next()
                res.append(n)
                count += 1
        except StopIteration:
            logger.info('last chunks reached')
            pass
        return res


class TilerManager:

    def __init__(self, configFile):
        tmsConfig = ConfigParser.RawConfigParser()
        tmsConfig.read(configFile)
        self.multiProcessing = int(tmsConfig.get('General', 'multiProcessing'))
        self.chunks = int(tmsConfig.get('General', 'chunks'))
        self.tmsConfig = tmsConfig

    def create(self):
        self.t0 = time.time()

        tilecount.value = 0
        skipcount.value = 0

        jobs = Jobs(self.tmsConfig, self.t0)

        if self.multiProcessing > 0:
            pool = multiprocessing.Pool(NUMBER_POOL_PROCESSES, initWorker)

            chunker = Chunks(jobs)

            chunks = chunker.nextX(self.chunks)
            bail = False
            while len(chunks) > 0 and not bail:
                logger.info('Processing %s jobs...' % str(len(chunks)))
                async = pool.map_async(worker, chunks, 1)
                try:
                    while not async.ready():
                        time.sleep(3)
                except KeyboardInterrupt:
                    logger.info('Keyboard interupt recieved, terminating workers...')
                    pool.terminate()
                    pool.join()
                    bail = True
                except Exception as e:
                    logger.error('Error while generating the tiles: %s' % e)
                    logger.error('Terminating workers...')
                    pool.terminate()
                    pool.join()
                    raise Exception(e)
                logger.info('Getting next jobs')
                chunks = chunker.nextX(self.chunks)
            if not bail:
                logger.info('All jobs have been completed.')
                logger.info('Closing processes...')
                pool.close()
                pool.join()
        else:
            for j in jobs:
                try:
                    worker(j)
                except Exception as e:
                    logger.error('An error occured while generating the tile: %s', e)
                    raise Exception(e)

        tend = time.time()
        logger.info('It took %s to create %s tiles (%s were skipped)' % (
            str(datetime.timedelta(seconds=tend - self.t0)), tilecount.value, skipcount.value))

    def stats(self):
        self.t0 = time.time()

        msg = '\n'
        jobs = Jobs(self.tmsConfig, self.t0)
        geodetic = GlobalGeodetic(True)
        bounds = (jobs.minLon, jobs.minLat, jobs.maxLon, jobs.maxLat)
        zooms = range(jobs.tileMinZ, jobs.tileMaxZ + 1)
        modelsPyramid = prepareModelsPyramid(jobs.tileMinZ, jobs.tileMaxZ, jobs.tmsConfig)

        db = DB('database.cfg')
        self.DBSession = scoped_session(sessionmaker(bind=db.userEngine))

        for i in xrange(0, len(zooms)):
            zoom = zooms[i]
            model = modelsPyramid[str(zoom)]
            nbObjects = self.DBSession.query(model).filter(model.bboxIntersects(bounds)).count()
            tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], zoom)
            tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], zoom)
            # Fast approach, but might not be fully correct
            if jobs.fullonly == 1:
                tileMinX += 1
                tileMinY += 1
                tileMaxX -= 1
                tileMaxY -= 1
            tileBounds = geodetic.TileBounds(tileMinX, tileMinY, zoom)
            xCount = tileMaxX - tileMinX + 1
            yCount = tileMaxY - tileMinY + 1
            nbTiles = xCount * yCount
            pointA = transformCoordinate('POINT(%s %s)' % (tileBounds[0], tileBounds[1]), 4326, 21781).GetPoints()[0]
            pointB = transformCoordinate('POINT(%s %s)' % (tileBounds[2], tileBounds[3]), 4326, 21781).GetPoints()[0]
            length = c2d.distance(pointA, pointB)
            if jobs.fullonly == 1:
                msg += 'WARNING: stats are approximative because fullonly is activated!\n'
            msg += 'At zoom %s:\n' % zoom
            msg += 'We expect %s tiles overall\n' % nbTiles
            msg += 'Min X is %s, Max X is %s\n' % (tileMinX, tileMaxX)
            msg += '%s columns over X\n' % xCount
            msg += 'Min Y is %s, Max Y is %s\n' % (tileMinY, tileMaxY)
            msg += '%s rows over Y\n' % yCount
            msg += '\n'
            msg += 'A tile side is around %s meters long\n' % int(round(length))
            if nbTiles > 0:
                msg += 'We have an average of about %s triangles per tile\n' % int(round(nbObjects / nbTiles))
            msg += '\n'

        logger.info(msg)
