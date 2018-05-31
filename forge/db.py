# -*- coding: utf-8 -*-

import os
import datetime
import time
import math
import subprocess
import sys
import ConfigParser
import sqlalchemy
import multiprocessing
from sqlalchemy.sql import exists, select, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from quantized_mesh_tile.global_geodetic import GlobalGeodetic
from poolmanager import PoolManager

from forge.configs import tmsConfig
import forge.lib.cartesian2d as c2d
from forge.models import create_simplified_geom_table
from forge.lib.tiles import TerrainTiles
from forge.models.tables import modelsPyramid, Lakes
from forge.lib.logs import getLogger
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.helpers import BulkInsert, timestamp
from forge.lib.helpers import cleanup, transformCoordinate


loggingConfig = ConfigParser.RawConfigParser()
loggingConfig.read('logging.cfg')
logger = getLogger(loggingConfig, __name__, suffix='db_%s' % timestamp())


# Create pickable object
class PopulateFeaturesArguments(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def reprojectShp(shpFilePath, args):
    logger.info('Action reprojectShapefile(%s)' % shpFilePath)
    outDirectory = args.outDirectory
    outFile = '%s%s' % (outDirectory, os.path.basename(shpFilePath))

    try:
        # If out file already exists clean it up first
        cleanup(outFile)

        command = 'mono %(geosuiteCmd)s -calc reframe -in %(inFile)s ' \
            '-out %(outFile)s -pframes %(fromPFrames)s,%(toPFrames)s ' \
            '-aframes %(fromAFrames)s,%(toAFrames)s -log %(logfile)s ' \
            '-err %(errorfile)s' % dict(
                geosuiteCmd = args.geosuiteCmd,
                inFile      = args.shpFile,
                outFile     = outFile,
                fromPFrames = args.fromPFrames,
                toPFrames   = args.toPFrames,
                fromAFrames = args.fromAFrames,
                toAFrames   = args.toAFrames,
                logfile     = args.logfile,
                errorfile   = args.errorfile
            )
        logger.info('Command: %s' % command)
        subprocess.call(command, shell=True)
    except Exception as e:
        logger.error('Could not reproject %(inFile)s into '
            '%(outFile)s: %(err)s' % dict(
                inFile  = shpFilePath,
                outFile = outFile,
                err     = e
            ), exc_info=True)
        raise Exception(e)

    # TODO new version has error codes this can now be changed
    # As we can't detect a success from an error with the current implementation
    # We determine if the output file exists and exit if not
    if not os.path.isfile(outFile):
        logger.error('File could not be reprojected')
        logger.error('Have a look at %(logfile)s or %(errorfile)s for '
            'more information.' % dict(
                logfile   = args.logfile,
                errorfile = args.errorfile
            ))
        raise Exception('File could not be reprojected!!')

    return outFile


def populateFeatures(args):
    pid = os.getpid()
    session = None
    shpFile = args.shpFile
    reproject = args.reproject
    keepfiles = args.keepfiles

    if reproject:
        try:
            shpFile = reprojectShp(shpFile, args)
        except Exception as e:
            raise Exception(e)

    try:
        models = modelsPyramid.models
        engine = sqlalchemy.create_engine(args.engineURL)
        session = scoped_session(sessionmaker(bind=engine))
        model = models[args.modelIndex]

        if not os.path.exists(shpFile):
            logger.error('[%s]: Shapefile %s does not exists' % (pid, shpFile))
            sys.exit(1)

        count = 1
        shp = ShpToGDALFeatures(shpFile)
        logger.info('[%s]: Processing %s' % (pid, shpFile))
        bulk = BulkInsert(model, session, withAutoCommit=1000)
        for feature in shp.getFeatures():
            polygon = feature.GetGeometryRef()
            # add shapefile path to dict
            # self.shpFilePath
            bulk.add(dict(
                shapefilepath=shpFile,
                the_geom='SRID=4326;' + polygon.ExportToWkt()
            ))
            count += 1
        bulk.commit()
        logger.info('[%s]: Commit %s features for %s.' % (pid, count, shpFile))
    except Exception as e:
        logger.error(e, exc_info=True)
        raise Exception(e)
    finally:
        if session is not None:
            session.close_all()
            engine.dispose()

    if reproject:
        # Discard file after reprojection if specified in config
        if not keepfiles:
            logger.info('[%s] Removing %s...' % (pid, shpFile))
            cleanup(shpFile)

    return count


class DB:

    class Server:

        def __init__(self, config):
            self.host = config.get('Server', 'host')
            self.port = config.getint('Server', 'port')

    class Admin:

        def __init__(self, config):
            self.user = config.get('Admin', 'user')
            self.password = config.get('Admin', 'password')

    class Database:

        def __init__(self, config):
            self.name = config.get('Database', 'name')
            self.user = config.get('Database', 'user')
            self.password = config.get('Database', 'password')

    def __init__(self, dbConfigFile):

        if not os.path.exists(dbConfigFile):
            raise OSError('%s not found' % dbConfigFile)
        self.dbConfigFile = dbConfigFile
        config = ConfigParser.RawConfigParser()
        config.read(dbConfigFile)
        self.config = config

        self.serverConf = DB.Server(config)
        self.adminConf = DB.Admin(config)
        self.databaseConf = DB.Database(config)

        connInfo = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s' \
                   ':%(port)d/%(database)s'
        self.superEngine = sqlalchemy.create_engine(
            connInfo % dict(
                user=self.adminConf.user,
                password=self.adminConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database='postgres'
            )
        )
        self.adminEngine = sqlalchemy.create_engine(
            connInfo % dict(
                user=self.adminConf.user,
                password=self.adminConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database=self.databaseConf.name
            )
        )
        self.userEngine = sqlalchemy.create_engine(
            connInfo % dict(
                user=self.databaseConf.user,
                password=self.databaseConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database=self.databaseConf.name,
                poolclass=NullPool
            )
        )

    @contextmanager
    def superConnection(self):
        conn = self.superEngine.connect()
        isolation = conn.connection.connection.isolation_level
        conn.connection.connection.set_isolation_level(0)
        yield conn
        conn.connection.connection.set_isolation_level(isolation)
        conn.close()

    @contextmanager
    def adminConnection(self):
        conn = self.adminEngine.connect()
        isolation = conn.connection.connection.isolation_level
        conn.connection.connection.set_isolation_level(0)
        yield conn
        conn.connection.connection.set_isolation_level(isolation)
        conn.close()

    @contextmanager
    def userConnection(self):
        conn = self.userEngine.connect()
        yield conn
        conn.close()

    @contextmanager
    def userSession(self):
        session = scoped_session(sessionmaker(bind=self.userEngine))
        yield session
        session.close()

    def createUser(self):
        self.dropUser()
        logger.info('Action: createUser()')
        logger.info('UserName: %s' % self.databaseConf.user)
        logger.info('UserPass: %s' % self.databaseConf.password)
        with self.superConnection() as conn:
            try:
                conn.execute("CREATE ROLE %(role)s WITH NOSUPERUSER "
                    "INHERIT LOGIN ENCRYPTED PASSWORD '%(password)s'" % dict(
                        role=self.databaseConf.user,
                        password=self.databaseConf.password
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not create user %(role)s: %(err)s' % dict(
                    role=self.databaseConf.user,
                    err=str(e)
                ), exc_info=True)

    def createDatabase(self):
        logger.info('Action: createDatabase()')
        logger.info('DBHost: %s' % self.serverConf.host)
        logger.info('DBName: %s' % self.databaseConf.name)
        with self.superConnection() as conn:
            try:
                conn.execute("CREATE DATABASE %(name)s WITH OWNER %(role)s "
                    "ENCODING 'UTF8'" % dict(
                        name=self.databaseConf.name,
                        role=self.databaseConf.user
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not create database %(name)s '
                    'with owner %(role)s: %(err)s' % dict(
                        name=self.databaseConf.name,
                        role=self.databaseConf.user,
                        err=str(e)
                    ), exc_info=True)

        with self.adminConnection() as conn:
            # WITH PostgreSQL 9.1+
            try:
                conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            except ProgrammingError as e:
                logger.error(
                    'Could not create postgis extension',
                    exc_info=True)
            try:
                conn.execute("""
                    ALTER SCHEMA public OWNER TO %(role)s;
                    ALTER TABLE public.spatial_ref_sys OWNER TO %(role)s;
                    ALTER TABLE public.geometry_columns OWNER TO %(role)s
                """ % dict(
                    role=self.databaseConf.user
                ))
            except ProgrammingError as e:
                logger.error('Could not create database %(name)s '
                    'with owner %(role)s: %(err)s' % dict(
                        name=self.databaseConf.name,
                        role=self.databaseConf.user,
                        err=str(e)
                    ), exc_info=True)

    def createSchema(self):
        logger.info('Action: createSchema()')
        with self.userSession() as session:
            q = exists(select([text("schema_name")])).select_from(
                text("information_schema.schemata")
            ).where(text("schema_name = 'data'"))
            if not session.query(q).scalar():
                logger.info('Creating schema data')
                session.execute('CREATE SCHEMA data;')
                session.commit()

    def createTables(self):
        logger.info('Action: createTables()')
        try:
            for model in modelsPyramid.models:
                model.__table__.create(self.userEngine, checkfirst=True)
            Lakes.__table__.create(self.userEngine, checkfirst=True)
        except ProgrammingError as e:
            logger.warning('Could not setup database on %(name)s'
                ': %(err)s' % dict(
                    name=self.databaseConf.name,
                    err=str(e)
                ))

    def setupDatabase(self):
        logger.info('Action: setupDatabase()')
        self.createSchema()
        self.createTables()

    def setupFunctions(self):
        logger.info('Action: setupFunctions()')
        logger.info('DBHost: %s' % self.serverConf.host)
        baseDir = 'forge/sql/'

        for fileName in os.listdir('forge/sql/'):
            logger.info('Action: setupFunctions() %s function' % fileName)
            if fileName != 'legacy.sql':
                command = 'psql --quiet -U %(user)s -d %(dbname)s -a -f ' \
                    '%(baseDir)s%(fileName)s' % dict(
                        user=self.databaseConf.user,
                        dbname=self.databaseConf.name,
                        baseDir=baseDir,
                        fileName=fileName
                    )
                try:
                    os.environ['PGPASSWORD'] = self.databaseConf.password
                    subprocess.call(command, shell=True)
                except Exception as e:
                    logger.error('Could not add custom functions '
                        '%s to the database: %(err)s' % dict(
                            fileName=fileName,
                            err=str(e)
                        ), exc_info=True)
                    logger.error(command)
                finally:
                    del os.environ['PGPASSWORD']
            else:
                pgVersion = ''
                with self.userConnection() as conn:
                    pgVersion = conn.execute(
                        "SELECT postgis_version();"
                    ).fetchone()[0]
                if pgVersion.startswith("2."):
                    command = 'psql --quiet -h %(host)s -U %(user)s ' \
                        '-d %(dbname)s -f %(baseDir)s%(fileName)s' % dict(
                            host=self.serverConf.host,
                            user=self.adminConf.user,
                            dbname=self.databaseConf.name,
                            baseDir=baseDir,
                            fileName=fileName
                        )
                    # We need an admin pass for untrusted language
                    try:
                        os.environ['PGPASSWORD'] = self.adminConf.password
                        subprocess.call(command, shell=True)
                    except Exception as e:
                        logger.error('Could not install postgis 2.1 '
                            'legacy functions to the database: '
                            '%(err)s' % dict(
                                err=str(e)
                            ), exc_info=True)
                        logger.error(command)
                    finally:
                        del os.environ['PGPASSWORD']

    def populateTables(self):
        logger.info('Action: populateTables()')

        reproject    = self.config.get('Reprojection', 'reproject')
        keepfiles    = self.config.get('Reprojection', 'keepfiles')
        outDirectory = self.config.get('Reprojection', 'outDirectory')
        geosuiteCmd  = self.config.get('Reprojection', 'geosuiteCmd')
        fromPFrames  = self.config.get('Reprojection', 'fromPFrames')
        toPFrames    = self.config.get('Reprojection', 'toPFrames')
        fromAFrames  = self.config.get('Reprojection', 'fromAFrames')
        toAFrames    = self.config.get('Reprojection', 'toAFrames')
        logfile      = self.config.get('Reprojection', 'logfile')
        errorfile    = self.config.get('Reprojection', 'errorfile')

        if not os.path.exists(outDirectory):
            raise OSError('%s does not exist' % outDirectory)
        if not os.path.exists(geosuiteCmd):
            raise OSError('%s does not exist' % geosuiteCmd)

        tstart = time.time()
        models = modelsPyramid.models
        featuresArgs = []
        for i in range(0, len(models)):
            model = models[i]
            for shp in model.__shapefiles__:

                featuresArgs.append(PopulateFeaturesArguments(
                    engineURL    = self.userEngine.url,
                    modelIndex   = i,
                    shpFile      = shp,
                    reproject    = True if reproject == '1' else False,
                    keepfiles    = True if keepfiles == '1' else False,
                    outDirectory = outDirectory,
                    geosuiteCmd  = geosuiteCmd,
                    fromPFrames  = fromPFrames,
                    toPFrames    = toPFrames,
                    fromAFrames  = fromAFrames,
                    toAFrames    = toAFrames,
                    logfile      = logfile,
                    errorfile    = errorfile
                ))

        cpuCount = multiprocessing.cpu_count()
        numFiles = len(featuresArgs)
        numProcs = cpuCount if numFiles >= cpuCount else numFiles
        pm = PoolManager(numProcs=numProcs, factor=1)
        pm.imap_unordered(populateFeatures, featuresArgs, 1)

        tend = time.time()
        logger.info('All tables have been created. It took %s' % str(
            datetime.timedelta(seconds=tend - tstart)))

    def populateLakes(self):
        self.setupDatabase()
        logger.info('Action: populateLakes()')

        # For now we never reproject lakes
        with self.userSession() as session:
            shpFile = self.config.get('Data', 'lakes')

            if not os.path.exists(shpFile):
                logger.error('Shapefile %s does not exists' % (shpFile))
                sys.exit(1)

            count = 1
            shp = ShpToGDALFeatures(shpFile)
            logger.info('Processing %s' % (shpFile))
            bulk = BulkInsert(Lakes, session, withAutoCommit=1000)

            for feature in shp.getFeatures():
                polygon = feature.GetGeometryRef()
                # Force 2D for lakes
                polygon.FlattenTo2D()
                # add shapefile path to dict
                # self.shpFilePath
                bulk.add(dict(
                    the_geom='SRID=4326;' + polygon.ExportToWkt()
                ))
                count += 1
            bulk.commit()
            logger.info('Commit %s features for %s.' % (count, shpFile))
            # Once all features have been commited, start creating all
            # the simplified versions of the lakes
            logger.info('Simplifying lakes')
            tiles = TerrainTiles(self.dbConfigFile, tmsConfig, time.time())
            geodetic = GlobalGeodetic(True)
            bounds = (tiles.minLon, tiles.minLat, tiles.maxLon, tiles.maxLat)
            zooms = range(tiles.tileMinZ, tiles.tileMaxZ + 1)
            for i in xrange(0, len(zooms)):
                zoom = zooms[i]
                tablename = 'lakes_%s' % zoom
                tileMinX, tileMinY = geodetic.LonLatToTile(
                    bounds[0], bounds[1], zoom
                )
                tileMaxX, tileMaxY = geodetic.LonLatToTile(
                    bounds[2], bounds[3], zoom
                )
                tileBounds = geodetic.TileBounds(tileMinX, tileMinY, zoom)
                pointA = transformCoordinate('POINT(%s %s)' % (
                    tileBounds[0], tileBounds[1]), 4326, 21781
                ).GetPoints()[0]
                pointB = transformCoordinate('POINT(%s %s)' % (
                    tileBounds[2], tileBounds[3]), 4326, 21781
                ).GetPoints()[0]
                length = c2d.distance(pointA, pointB)
                pixelArea = pow(length, 2) / pow(256.0, 2)
                pixelLength = math.sqrt(pixelArea)
                session.execute(
                    create_simplified_geom_table(tablename, pixelLength)
                )
                session.commit()
                logger.info('Commit table public.%s with %s meters '
                    'tolerance' % (tablename, pixelLength))

    def dropDatabase(self):
        logger.info('Action: dropDatabase()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "DROP DATABASE %(name)s" % dict(
                        name=self.databaseConf.name
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not drop database %(name)s: %(err)s' % dict(
                    name=self.databaseConf.name,
                    err=str(e)
                ), exc_info=True)

    def dropUser(self):
        logger.info('Action: dropUser()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "DROP ROLE IF EXISTS %(role)s" % dict(
                        role=self.databaseConf.user
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not drop user %(role)s: %(err)s' % dict(
                    role=self.databaseConf.user,
                    err=str(e)
                ), exc_info=True)

    def create(self):
        logger.info('Action: create()')
        self.createUser()
        self.createDB()

    def createDB(self):
        logger.info('Action: createDB()')
        self.createDatabase()
        self.setupDatabase()
        self.setupFunctions()

    def populate(self):
        logger.info('Action: populate()')
        # Create missing tables in case new ones were added
        self.setupDatabase()
        self.populateTables()

    def destroy(self):
        logger.info('Action: destroy()')
        self.dropDatabase()
        self.dropUser()

    def console(self):
        logger.info('Action: console()')
        try:
            os.environ['PGPASSWORD'] = self.databaseConf.password
            cmdline = 'psql -h %(host)s -p %(port)d -U %(user)s %(name)s' % dict(
                host    = self.serverConf.host,
                port    = self.serverConf.port,
                user    = self.databaseConf.user,
                name    = self.databaseConf.name
            )
            cmd = cmdline.split()
            os.spawnvpe(os.P_WAIT, cmd[0], cmd, os.environ)
        finally:
            del os.environ['PGPASSWORD']
