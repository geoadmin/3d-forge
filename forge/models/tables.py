# -*- coding: utf-8 -*-

import os
import ConfigParser
from sqlalchemy import Column, Sequence, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base

from forge.models import Vector, Geometry
from forge.lib.helpers import isShapefile


Base = declarative_base()

table_args = {'schema': 'data'}
# management to true only for postgis 1.5
WGS84Polygon3D = Geometry(
    geometry_type='POLYGON', srid=4326,
    dimension=3, spatial_index=True, management=True
)
WGS84Polygon2D = Geometry(
    geometry_type='POLYGON', srid=4326, dimension=2,
    spatial_index=True, management=True
)


class Lakes(Base, Vector):
    __tablename__ = 'lakes'
    __table_args__ = {'schema': 'public'}
    id = Column(
        BigInteger(), Sequence('id_lakes_seq', schema=table_args['schema']),
        nullable=False, primary_key=True
    )
    the_geom = Column('the_geom', WGS84Polygon2D)


def modelFactory(BaseClass, tablename, shapefiles, classname):
    sequence = Sequence('id_%s_seq' % tablename, schema=table_args['schema'])

    class NewClass(BaseClass, Vector):
        __tablename__ = tablename
        __table_args__ = table_args
        __shapefiles__ = shapefiles
        id = Column(BigInteger(), sequence, nullable=False, primary_key=True)
        shapefilepath = Column('shapefilepath', Text)
        the_geom = Column('the_geom', WGS84Polygon3D)
    NewClass.__name__ = classname
    return NewClass


class ModelsPyramid:

    def __init__(self, dbConfigFile, tmsConfigFile):
        dbConfig = ConfigParser.RawConfigParser()
        dbConfig.read(dbConfigFile)
        self.baseDir = dbConfig.get('Data', 'baseDir')
        self.shpsBaseDir = dbConfig.get('Data', 'shapefiles').split(',')
        self.tablenames = dbConfig.get('Data', 'tablenames').split(',')
        self.modelnames = dbConfig.get('Data', 'modelnames').split(',')
        self.tmsConfigFile = tmsConfigFile

        self.models = []
        self._createModels()

    def _createModels(self):
        for i in range(0, len(self.shpsBaseDir)):
            shpBaseDir = '%s%s' % (self.baseDir, self.shpsBaseDir[i])
            if os.path.exists(shpBaseDir):
                shapefiles = ['%s%s' % (shpBaseDir, f)
                    for f in os.listdir(shpBaseDir) if isShapefile(f)]
            else:
                shapefiles = []
            self.models.append(modelFactory(
                Base, self.tablenames[i], shapefiles, self.modelnames[i]
            ))

        self._buildModelsPyramid()

    def _buildModelsPyramid(self):
        tmsConfig = ConfigParser.RawConfigParser()
        tmsConfig.read(self.tmsConfigFile)
        self.tileMinZ = tmsConfig.getint('Zooms', 'tileMinZ')
        self.tileMaxZ = tmsConfig.getint('Zooms', 'tileMaxZ')

        self.modelsPyramid = {}
        for i in range(self.tileMinZ, self.tileMaxZ + 1):
            for j in range(0, len(self.models)):
                model = self.models[j]
                tableName = tmsConfig.get(str(i), 'tablename')
                if model.__tablename__ == tableName:
                    self.modelsPyramid[str(i)] = j
                    break

    def getModelByZoom(self, zoom):
        zoom = str(zoom)
        if zoom in self.modelsPyramid:
            return self.models[
                self.modelsPyramid[zoom]
            ]
        return None

    def getLakeModelByZoom(self, zoom):
        class LakeNewClass(Base, Vector):
            __tablename__ = 'lakes_%s' % zoom
            __table_args__ = {'schema': 'public', 'extend_existing': True}
            id = Column(BigInteger(), nullable=False, primary_key=True)
            the_geom = Column('the_geom', WGS84Polygon2D)
        return LakeNewClass


def isInside(tile, bounds):
    if tile[0] >= bounds[0] and tile[1] >= bounds[1] and tile[2] <= bounds[2] and tile[3] <= bounds[3]:
        return True
    return False


modelsPyramid = ModelsPyramid('configs/terrain/database.cfg',
    'configs/terrain/tms.cfg')
