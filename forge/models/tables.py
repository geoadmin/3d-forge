# -*- coding: utf-8 -*-

import os
import ConfigParser
from geoalchemy2 import Geometry
from sqlalchemy import event
from sqlalchemy.schema import CreateSchema
from sqlalchemy import Column, Sequence, Integer
from sqlalchemy.ext.declarative import declarative_base
from forge.models import Vector
from forge.lib.helpers import isShapefile


Base = declarative_base()
event.listen(Base.metadata, 'before_create', CreateSchema('data'))

models = []
table_args = {'schema': 'data'}
# management to true only for postgis 1.5
WGS84Polygon = Geometry(geometry_type='POLYGON', srid=4326, dimension=3, spatial_index=True, management=True)


def modelFactory(BaseClass, tablename, shapefiles, classname):
    sequence = Sequence('id_%s_seq' % tablename, schema=table_args['schema'])

    class NewClass(BaseClass, Vector):
        __tablename__ = tablename
        __table_args__ = table_args
        __shapefiles__ = shapefiles
        id = Column(Integer(), sequence, nullable=False, primary_key=True)
        the_geom = Column('the_geom', WGS84Polygon)
    NewClass.__name__ = classname
    return NewClass


def createModels(configFile):
    config = ConfigParser.RawConfigParser()
    config.read(configFile)
    baseDir = config.get('Data', 'baseDir')
    shpsBaseDir = config.get('Data', 'shapefiles').split(',')
    tablenames = config.get('Data', 'tablenames').split(',')
    modelnames = config.get('Data', 'modelnames').split(',')
    for i in range(0, len(shpsBaseDir)):
        shpBaseDir = '%s%s' % (baseDir, shpsBaseDir[i])
        shapefiles = ['%s%s' % (shpBaseDir, f) for f in os.listdir(shpBaseDir) if isShapefile(f)]
        models.append(modelFactory(
            Base, tablenames[i], shapefiles, modelnames[i]
        ))

createModels('database.cfg')
