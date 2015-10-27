# -*- coding: utf-8 -*-

import sys
import time
import datetime
import traceback
import sqlalchemy
import ConfigParser
from sqlalchemy import Column, BigInteger
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base

from forge.models import Vector, Geometry
from forge.terrain.metadata import TerrainMetadata
from forge.lib.tiles import Tiles


def scanLayer(tMeta, tile, session, model, tilecount, fromSrid, toSrid):
    try:
        (bounds, tileXYZ, t0, dbConfigFile, hasLighting, hasWatermask) = tile

        # Get the model according to the zoom level
        query = session.query(model.id).filter(model.bboxIntersects(bounds, fromSrid=fromSrid, toSrid=toSrid)).limit(1)
        try:
            query.one()
        except NoResultFound:
            tMeta.removeTile(tileXYZ[0], tileXYZ[1], tileXYZ[2])
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

    if tilecount % 1000 == 0:
        tend = time.time()
        print 'It took %s to scan %s tiles' % (str(datetime.timedelta(seconds=tend - t0)), tilecount)

    return tMeta


def getModel(BaseClass, VectorClass, tableName, dbSchema, pkColumnName, pkColumnType, toSrid):
    class RasterLayer(BaseClass, VectorClass):
        __tablename__ = tableName
        __table_args__ = {'schema': dbSchema}
        id = Column(pkColumnName, pkColumnType, primary_key=True)
        the_geom = Column(Geometry(geometry_type='GEOMETRY', dimension=2, srid=toSrid))
    return RasterLayer


layerName = 'ch.swisstopo.swisstlm3d-wanderwege'
fromSrid = 4326
toSrid = 21781

dbHost = 'pg-sandbox.bgdi.ch'
dbPort = 5432
dbUser = 'www-data'
dbPass = 'www-data'
dbName = 'stopo_dev'
dbSchema = 'karto'
tableName = 'wanderwege_swissmap'
pkColumnName = 'nr'

basePath = '1.0.0/' + layerName + '/default/20150101/'

baseUrls = [
    "//wmts9.geo.admin.ch/" + basePath + "{z}/{x}/{y}.png",
    "//wmts10.geo.admin.ch/" + basePath + "{z}/{x}/{y}.png",
    "//wmts11.geo.admin.ch/" + basePath + "{z}/{x}/{y}.png",
    "//wmts12.geo.admin.ch/" + basePath + "{z}/{x}/{y}.png",
    "//wmts13.geo.admin.ch/" + basePath + "{z}/{x}/{y}.png",
    "//wmts14.geo.admin.ch/" + basePath + "{z}/{x}/{y}.png"
]
Base = declarative_base()
engine = sqlalchemy.create_engine('postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
    user=dbUser,
    password=dbPass,
    host=dbHost,
    port=dbPort,
    database=dbName
))
session = scoped_session(sessionmaker(bind=engine))
t0 = time.time()
tmsConfig = ConfigParser.RawConfigParser()
tmsConfig.read('tms.cfg')
tiles = Tiles('database.cfg', tmsConfig, t0)
tMeta = TerrainMetadata(
    bounds=tiles.bounds, minzoom=tiles.tileMinZ, maxzoom=tiles.tileMaxZ,
    useGlobalTiles=False, hasLighting=tiles.hasLighting, hasWatermask=tiles.hasWatermask,
    baseUrls=baseUrls)

tilecount = 1
model = getModel(Base, Vector, tableName, dbSchema, pkColumnName, BigInteger, toSrid)

for tile in tiles:
    tMeta = scanLayer(tMeta, tile, session, model, tilecount, fromSrid, toSrid)
    tilecount += 1

session.close()
engine.dispose()
tend = time.time()
print'It took %s to scan %s tiles' % (str(datetime.timedelta(seconds=tend - t0)), tilecount)

with open('.tmp/layer.json', 'w') as f:
    f.write(tMeta.toJSON())
