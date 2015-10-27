# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import sqlalchemy
import cStringIO
import ConfigParser

from sqlalchemy import Column
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base

from forge.models import Vector, Geometry
from forge.layers.metadata import LayerMetadata
from forge.lib.helpers import timestamp
from forge.lib.tiles import Tiles
from forge.lib.logs import getLogger
from forge.lib.helpers import gzipFileObject
from forge.lib.boto_conn import getBucket, writeToS3


loggingConfig = ConfigParser.RawConfigParser()
loggingConfig.read('logging.cfg')
logger = getLogger(loggingConfig, __name__, suffix=timestamp())


Base = declarative_base()


def scanLayer(tile, session, model, sridFrom, sridTo, tilecount):
    try:
        (bounds, tileXYZ, t0) = tile
        # Get the model according to the zoom level
        query = session.query(model.id).filter(
            model.bboxIntersects(bounds, fromSrid=sridFrom, toSrid=sridTo)).limit(1)
        try:
            query.one()
        except NoResultFound:
            return tileXYZ
        finally:
            if tilecount % 1000 == 0:
                tend = time.time()
                logger.info(
                    'Last tile scanned was %s/%s/%s' % (tileXYZ[2], tileXYZ[0], tileXYZ[1]))
                logger.info('It took %s to scan %s tiles' % (
                    str(datetime.timedelta(seconds=tend - t0)), tilecount))
    except Exception as e:
        logger.error(e, exc_info=True)


def getOrmModel(pkColumnName, pkColumnType, tableName, dbSchema, toSrid):
    class RasterLayer(Base, Vector):
        __tablename__ = tableName
        __table_args__ = {'schema': dbSchema}
        id = Column(pkColumnName, pkColumnType, primary_key=True)
        the_geom = Column(Geometry(geometry_type='GEOMETRY', dimension=2, srid=toSrid))
    return RasterLayer


def main(template):
    try:
        dbConfig     = ConfigParser.RawConfigParser()
        dbConfig.read('configs/raster/database.cfg')
        dbHost       = dbConfig.get('Server', 'host')
        dbPort       = dbConfig.getint('Server', 'port')
        dbUser       = dbConfig.get('Server', 'user')
        dbPass       = dbConfig.get('Server', 'password')
    except ConfigParser.NoSectionError as e:
        logger.error(e, exc_info=True)
        raise ValueError('Configuration file in configs/raster/database.cfg contains errors.')

    try:
        layerConfig    = ConfigParser.RawConfigParser()
        layerConfig.read(template)
        dbName         = layerConfig.get('Database', 'dbName')
        dbSchema       = layerConfig.get('Database', 'dbSchema')
        tableName      = layerConfig.get('Database', 'tableName')
        bucketBasePath = layerConfig.get('Grid', 'bucketPath')
        sridFrom       = layerConfig.getint('Grid', 'sridFrom')
        sridTo         = layerConfig.getint('Grid', 'sridTo')
        # terrainBased   = layerConfig.get('Grid', 'terrainBased')
        # pxTolerance    = layerConfig.getint('Grid', 'pxTolerance')
        fullonly       = layerConfig.getint('Grid', 'fullonly')
        bounds         = layerConfig.get('Grid', 'bounds')
        bounds         = map(float, bounds.split(','))
        minZoom        = layerConfig.getint('Grid', 'minZoom')
        maxZoom        = layerConfig.getint('Grid', 'maxZoom')
        maxScanZoom    = layerConfig.getint('Grid', 'maxScanZoom')
        name           = layerConfig.get('Metadata', 'name')
        format         = layerConfig.get('Metadata', 'format')
        description    = layerConfig.get('Metadata', 'description')
        attribution    = layerConfig.get('Metadata', 'attribution')
        tilesURLs      = layerConfig.get('Metadata', 'tilesURLs')
        tilesURLs      = tilesURLs.split(',')
    except ConfigParser.NoSectionError as e:
        logger.error(e, exc_info=True)
        raise ValueError('The layer configuration file contains errors.')

    baseUrls = []
    for tURL in tilesURLs:
        baseUrls.append(tURL + bucketBasePath + "{z}/{x}/{y}." + format)

    def getEngine():
        connInfo = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s'
        engine = sqlalchemy.create_engine(connInfo % dict(
            user=dbUser,
            password=dbPass,
            host=dbHost,
            port=dbPort,
            database=dbName
        ))
        return engine

    tilecount = 0
    engine = getEngine()
    metadata = sqlalchemy.MetaData(bind=engine, schema=dbSchema)
    metadata.reflect()
    try:
        table = metadata.tables[dbSchema + '.' + tableName]
    except KeyError:
        raise ValueError('Table %s in schema %s could not be found' % (tableName, dbSchema))
    # We assume a pkey is defined by only one column for now.
    pkColumn = table.primary_key.columns.items()[0]
    pkColumnName = pkColumn[0].__str__()
    pkColumnType = pkColumn[1].type.__class__

    model = getOrmModel(pkColumnName, pkColumnType, tableName, dbSchema, sridTo)

    t0 = time.time()

    try:
        session = scoped_session(sessionmaker(bind=engine))
        # We usually don't scan the last levels
        tiles = Tiles(bounds, minZoom, maxScanZoom, t0, fullonly)
        tMeta = LayerMetadata(
            bounds=bounds, minzoom=minZoom, maxzoom=maxZoom, baseUrls=baseUrls,
            description=description, attribution=attribution, name=name)
        for tile in tiles:
            tilecount += 1
            noGeom = scanLayer(tile, session, model, sridFrom, sridTo, tilecount)
            if noGeom:
                tMeta.removeTile(noGeom[0], noGeom[1], noGeom[2])
    finally:
        session.close()
        engine.dispose()

    # Same bucket for now
    bucket = getBucket()
    fileObj = cStringIO.StringIO()
    fileObj.write(tMeta.toJSON())
    fileObj = gzipFileObject(fileObj)
    logger.info('Uploading %s/layer.json to S3' % bucketBasePath)
    writeToS3(bucket, 'layer.json', fileObj,
        bucketBasePath, 'application/json')
    logger.info('layer.json has been uploaded successfully')

    tend = time.time()
    logger.info('It took %s to scan %s tiles' % (
        str(datetime.timedelta(seconds=tend - t0)), tilecount))


if __name__ == '__main__':
    args = sys.argv[1:]
    template = args[0]
    if not os.path.exists(template):
        logger.error('Could not find %s!' % template)
        sys.exit()
    main(template)
