# -*- coding: utf-8 -*-

import ConfigParser
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
models = []
table_args = {'schema': 'public'}
WGS84Polygon = Geometry(geometry_type='POLYGON', srid=4326, dimension=3, spatial_index=True)


def modelFactory(BaseClass, tablename, shapefile, classname):
    class NewClass(BaseClass):
        __tablename__ = tablename
        __table_args__ = table_args
        __shapefile__ = shapefile
        id = Column(Integer(), nullable=False, primary_key=True)
        geom = WGS84Polygon
    NewClass.__name__ = classname
    return NewClass


def createModels(configFile):
    config = ConfigParser.RawConfigParser()
    config.read(configFile)
    tablenames = config.get('Data', 'tablenames').split(',')
    shapefiles = config.get('Data', 'shapefiles').split(',')
    modelnames = config.get('Data', 'modelnames').split(',')
    for i in range(0, len(shapefiles)):
        models.append(modelFactory(
            Base, tablenames[i], shapefiles[i], modelnames[i]
        ))

createModels('database.cfg')
