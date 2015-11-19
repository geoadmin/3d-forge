# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import random
import datetime
import sqlalchemy
import cStringIO
import ConfigParser
import multiprocessing

from sqlalchemy import Column
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry

from forge.models import Vector, tableExtentLiteral
from forge.lib.global_geodetic import GlobalGeodetic
from forge.layers.metadata import LayerMetadata
from forge.lib.helpers import timestamp
from forge.lib.tiles import Tiles
from forge.lib.logs import getLogger
from forge.lib.helpers import gzipFileObject, resourceExists
from forge.lib.boto_conn import getBucket, writeToS3
from forge.lib.poolmanager import PoolManager


loggingConfig = ConfigParser.RawConfigParser()
loggingConfig.read('logging.cfg')
logger = getLogger(loggingConfig, __name__, suffix=timestamp())


Base = declarative_base()


def scanLayer(tile, session, model, sridFrom, sridTo, tilecount):
    try:
        (bounds, tileXYZ, t0) = tile
        # Get the model according to the zoom level
        query = session.query(model.id).filter(
            model.bboxIntersects(
                bounds, fromSrid=sridFrom, toSrid=sridTo)).limit(1)
        try:
            query.one()
        except NoResultFound:
            return tileXYZ
        finally:
            if tilecount % 1000 == 0:
                tend = time.time()
                logger.info(
                    'Last tile scanned was %s/%s/%s' % (
                        tileXYZ[2], tileXYZ[0], tileXYZ[1]))
                logger.info('It took %s to scan %s tiles' % (
                    str(datetime.timedelta(seconds=tend - t0)), tilecount))
    except Exception as e:
        logger.error(e, exc_info=True)


def getEngine(params):
    connInfo = 'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:' \
        '%(port)d/%(database)s'
    engine = sqlalchemy.create_engine(connInfo % dict(
        user=params.dbUser,
        password=params.dbPass,
        host=params.dbHost,
        port=params.dbPort,
        database=params.dbName
    ))
    return engine


def getOrmModel(pkColumnName, pkColumnType, params):
    class ModelBasedLayer(Base, Vector):
        __tablename__ = params.tableName
        __table_args__ = {'schema': params.dbSchema}
        id = Column(pkColumnName, pkColumnType, primary_key=True)
        the_geom = Column(
            Geometry(geometry_type='GEOMETRY', dimension=2, srid=params.sridTo)
        )
    return ModelBasedLayer


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def parseModelBasedLayer(dbConfig, layerConfig):
    try:
        return AttributeDict(
            dbHost         = dbConfig.get('Server', 'host'),
            dbPort         = dbConfig.getint('Server', 'port'),
            dbUser         = dbConfig.get('Server', 'user'),
            dbPass         = dbConfig.get('Server', 'password'),
            dbName         = layerConfig.get('Database', 'dbName'),
            dbSchema       = layerConfig.get('Database', 'dbSchema'),
            tableName      = layerConfig.get('Database', 'tableName'),
            gridOrigin     = layerConfig.get('Grid', 'gridOrigin'),
            bucketBasePath = layerConfig.get('Grid', 'bucketPath'),
            sridFrom       = layerConfig.getint('Grid', 'sridFrom'),
            sridTo         = layerConfig.getint('Grid', 'sridTo'),
            pxTolerance    = layerConfig.getint('Grid', 'pxTolerance'),
            fullonly       = layerConfig.getint('Grid', 'fullonly'),
            bounds         = map(float,
                layerConfig.get('Grid', 'bounds').split(',')),
            minZoom        = layerConfig.getint('Grid', 'minZoom'),
            maxZoom        = layerConfig.getint('Grid', 'maxZoom'),
            maxScanZoom    = layerConfig.getint('Grid', 'maxScanZoom'),
            name           = layerConfig.get('Metadata', 'name'),
            format         = layerConfig.get('Metadata', 'format'),
            tileTemplate   = layerConfig.get('Metadata', 'tileTemplate'),
            description    = layerConfig.get('Metadata', 'description'),
            attribution    = layerConfig.get('Metadata', 'attribution'),
            tilesURLs      = layerConfig.get('Metadata', 'tilesURLs').split(',')
        )
    except ConfigParser.NoSectionError as e:
        logger.error(e, exc_info=True)
        raise ValueError('The configurations file may contain errors.')


def parseTerrainBasedLayer(layerConfig):
    try:
        return AttributeDict(
            gridOrigin     = layerConfig.get('Grid', 'gridOrigin'),
            bucketBasePath = layerConfig.get('Grid', 'bucketPath'),
            bounds         = map(float,
                layerConfig.get('Grid', 'bounds').split(',')),
            minZoom        = layerConfig.getint('Grid', 'minZoom'),
            maxZoom        = layerConfig.getint('Grid', 'maxZoom'),
            maxScanZoom    = layerConfig.getint('Grid', 'maxScanZoom'),
            fullonly       = layerConfig.getint('Grid', 'fullonly'),
            name           = layerConfig.get('Metadata', 'name'),
            format         = layerConfig.get('Metadata', 'format'),
            tileTemplate   = layerConfig.get('Metadata', 'tileTemplate'),
            description    = layerConfig.get('Metadata', 'description'),
            attribution    = layerConfig.get('Metadata', 'attribution'),
            tilesURLs      = layerConfig.get('Metadata', 'tilesURLs').split(',')
        )
    except ConfigParser.NoSectionError as e:
        logger.error(e, exc_info=True)
        raise ValueError('The layer configuration file contains errors.')


def getBaseUrls(params):
    baseUrls = []
    for tURL in params.tilesURLs:
        baseUrls.append(
            tURL + params.bucketBasePath + params.tileTemplate + "." + params.format
        )
    return baseUrls


def createModelBasedTileJSON(params):
    tilecount = 0
    t0 = time.time()
    baseUrls = getBaseUrls(params)

    engine = getEngine(params)
    metadata = sqlalchemy.MetaData(bind=engine, schema=params.dbSchema)
    metadata.reflect()
    try:
        table = metadata.tables[params.dbSchema + '.' + params.tableName]
    except KeyError:
        raise ValueError(
            'Table %s in schema %s could not be found' % (
                params.tableName, params.dbSchema))
    # We assume a pkey is defined by only one column for now.
    pkColumn = table.primary_key.columns.items()[0]
    pkColumnName = pkColumn[0].__str__()
    pkColumnType = pkColumn[1].type.__class__
    model = getOrmModel(pkColumnName, pkColumnType, params)
    # Bounds generated from DB
    try:
        conn = engine.connect()
        bounds = conn.execute(
            tableExtentLiteral(params.dbSchema, params.tableName, params.sridFrom)
        ).fetchone()
        strBounds = tuple(['{:2f}'.format(i) for i in bounds])
        logger.info('Bounds are %s, %s, %s, %s' % strBounds)
    except Exception as e:
        logger.error('An error occured while determining the bounds', exc_info=True)
        raise Exception(e)
    finally:
        conn.close()

    try:
        session = scoped_session(sessionmaker(bind=engine))
        # We usually don't scan the last levels
        tiles = Tiles(
            bounds, params.minZoom, params.maxScanZoom,
            t0, params.fullonly
        )
        tMeta = LayerMetadata(
            bounds=bounds, minzoom=params.minZoom,
            maxzoom=params.maxZoom, baseUrls=baseUrls,
            description=params.description, attribution=params.attribution,
            name=params.name
        )
        for tile in tiles:
            tilecount += 1
            noGeom = scanLayer(
                tile, session, model, params.sridFrom, params.sridTo, tilecount
            )
            if noGeom:
                tMeta.removeTile(noGeom[0], noGeom[1], noGeom[2])
    finally:
        session.close()
        engine.dispose()
    return (tMeta.toJSON(), tilecount)


def createTerrainBasedTileJSON(params):
    baseUrls = getBaseUrls(params)
    with open('configs/terrain/layer.json') as f:
        terrainConfig = json.loads(f.read())

    # Delete unrelevant fields
    if 'extensions' in terrainConfig:
        del terrainConfig['extensions']
    # Overwrite
    terrainConfig['bounds'] = params.bounds
    terrainConfig['minzoom'] = params.minZoom
    terrainConfig['maxzoom'] = params.maxZoom
    terrainConfig['name'] = params.name
    terrainConfig['format'] = params.format
    terrainConfig['description'] = params.description
    terrainConfig['attribution'] = params.attribution
    terrainConfig['tiles'] = baseUrls

    geodetic = GlobalGeodetic(True)
    # Fix with empty ranges if we start with a biggeer min zoom
    for i in range(0, params.maxZoom + 1):
        if i < params.minZoom:
            terrainConfig['available'][i] = []
        # Max zoom is heigher than max terrain zoom level
        # In that case we include the full range within the bounds
        if i >= len(terrainConfig['available']):
            tileMinX, tileMinY = geodetic.LonLatToTile(
                params.bounds[0], params.bounds[1], i
            )
            tileMaxX, tileMaxY = geodetic.LonLatToTile(
                params.bounds[2], params.bounds[3], i
            )
            terrainConfig['available'].append(dict(
                startX=tileMinX,
                endX=tileMaxX,
                startY=tileMinY,
                endY=tileMaxY
            ))
    return json.dumps(terrainConfig)

tilecount = multiprocessing.Value('i', 0)
tileskipped = multiprocessing.Value('i', 0)
# Return None if the tile exists and a list with x,y,z coordinates otherwise


def tileNotExists(tile):
    h = {'Referer': 'http://geo.admin.ch'}
    (bounds, tileXYZ, t0, basePath, tFormat, gridOrigin, tilesURLs) = tile
    # Only native tiles for now
    entryPoint = 'http:%s' % (random.choice(tilesURLs))

    # Account for a different origin
    if gridOrigin == 'topLeft':
        geodetic = GlobalGeodetic(True)
        nbYTiles = geodetic.GetNumberOfYTilesAtZoom(tileXYZ[2])
        tilexyz = (tileXYZ[0], nbYTiles - tileXYZ[1] - 1, tileXYZ[2])
        tileAdress = '/'.join((str(tilexyz[2]), str(tilexyz[1]), str(tilexyz[0])))
    else:
        tileAdress = '/'.join((str(tileXYZ[2]), str(tileXYZ[1]), str(tileXYZ[0])))

    url = '%s%s%s.%s' % (entryPoint, basePath, tileAdress, tFormat)
    tilecount.value += 1

    try:
        exists = resourceExists(url, headers=h)
    except Exception as e:
        logger.error('Connection Error', exc_info=True)
        logger.error('%s was skipped' % url, exc_info=True)
        raise Exception(e)

    if not exists:
        tileskipped.value += 1
    if tilecount.value % 1000 == 0:
        tend = time.time()
        logger.info('It took %s to (HEAD) request %s tiles. %s skipped' % (
            str(datetime.timedelta(seconds=tend - t0)),
            tilecount.value, tileskipped.value)
        )
        logger.info('Last tile checked:')
        logger.info(url)
    if not exists:
        # Return everything in terrain coordinates
        # e.g. starting at the bottom left (Transformation is performed in Cesium)
        # https://github.com/camptocamp/cesium/blob/c2c_patches/Source/
        #     Scene/UrlTemplateImageryProvider.js#L500
        return tileXYZ


def createS3BasedTileJSON(params):
    t0 = time.time()
    maxChunks = 50
    baseUrls = getBaseUrls(params)
    tiles = Tiles(
        params.bounds, params.minZoom, params.maxScanZoom,
        t0, fullonly=params.fullonly, basePath=params.bucketBasePath,
        tFormat=params.format, gridOrigin=params.gridOrigin,
        tilesURLs=params.tilesURLs
    )
    pm = PoolManager(logger=logger, factor=1, store=True)
    tMeta = LayerMetadata(
        bounds=params.bounds, minzoom=params.minZoom,
        maxzoom=params.maxZoom, baseUrls=baseUrls,
        description=params.description, attribution=params.attribution,
        format=params.format, name=params.name
    )
    pm.process(tiles, tileNotExists, maxChunks)
    for xyz in pm.results:
        tMeta.removeTile(xyz[0], xyz[1], xyz[2])
    return tMeta.toJSON()


def main(template):
    t0 = time.time()
    tilecount = None
    layerConfig = ConfigParser.RawConfigParser()
    layerConfig.read(template)
    try:
        terrainBased = layerConfig.getboolean('Grid', 'terrainBased')
    except ConfigParser.NoSectionError as e:
        logger.error(e, exc_info=True)
        raise ValueError('The layer configuration file contains errors.')

    if terrainBased:
        # params = parseTerrainBasedLayer(layerConfig)
        # tileJSON = createTerrainBasedTileJSON(params)
        params = parseTerrainBasedLayer(layerConfig)
        tileJSON = createS3BasedTileJSON(params)
    else:
        dbConfig = ConfigParser.RawConfigParser()
        dbConfig.read('configs/raster/database.cfg')
        params = parseModelBasedLayer(dbConfig, layerConfig)
        (tileJSON, tilecount) = createModelBasedTileJSON(params)

    # Same bucket for now
    bucket = getBucket()
    fileObj = cStringIO.StringIO()
    fileObj.write(tileJSON)
    fileObj = gzipFileObject(fileObj)
    logger.info('Uploading %slayer.json to S3' % params.bucketBasePath)

    writeToS3(bucket, 'layer.json', fileObj, 'tilejson', params.bucketBasePath,
        contentType='application/json')
    logger.info('layer.json has been uploaded successfully')

    if tilecount:
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
