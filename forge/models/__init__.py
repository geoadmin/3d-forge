# -*- coding: utf-8 -*-

from sqlalchemy.sql import func, and_
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement
from geoalchemy2.elements import WKBElement
from geoalchemy2.types import Geometry as GeoAlchemyGeometry
from shapely.geometry import box, Point


class Geometry(GeoAlchemyGeometry):

    def column_expression(self, col):
        return func.ST_AsEWKB(col, type_=self)


class _interpolate_height_on_plane(FunctionElement):
    name = "_interpolate_height_on_plane"


@compiles(_interpolate_height_on_plane)
def compile(element, compiler, **kw):
    return "_interpolate_height_on_plane(%s)" % compiler.process(element.clauses)


class Vector(object):

    @classmethod
    def primaryKeyColumn(cls):
        return cls.__mapper__.primary_key[0]

    @classmethod
    def geometryColumn(cls):
        return cls.__mapper__.columns['the_geom']

    """
    Returns a sqlalchemy.sql.functions.Function clipping function
    :param bbox: A list of 4 coordinates [minX, minY, maxX, maxY]
    """
    @classmethod
    def bboxClippedGeom(cls, bbox, srid=4326):
        bboxGeom = shapelyBBox(bbox)
        wkbGeometry = WKBElement(buffer(bboxGeom.wkb), srid)
        geomColumn = cls.geometryColumn()
        return func.ST_Intersection(geomColumn, wkbGeometry)

    """
    Returns a slqalchemy.sql.functions.Function (interesects function)
    Use it as a filter to determine if a geometry should be returned (True or False)
    :params bbox: A list of 4 coordinates [minX, minX, maxX, maxY]
    """
    @classmethod
    def bboxIntersects(cls, bbox, srid=4326):
        bboxGeom = shapelyBBox(bbox)
        wkbGeometry = WKBElement(buffer(bboxGeom.wkb), srid)
        geomColumn = cls.geometryColumn()
        return and_(geomColumn.intersects(wkbGeometry), func.ST_Intersects(geomColumn, wkbGeometry))

    """
    Returns a slqalchemy.sql.functions.Function (interesects function)
    Use it as a point filter to determine if a geometry should be returned (True or False)
    :params point: A list of dim 3 representing one point [X, Y, Z]
    :params geomColumn: A sqlAlchemy Column representing a postgis geometry (Optional)
    """
    @classmethod
    def pointIntersects(cls, point, geomColumn=None, srid=4326):
        pointGeom = Point(point)
        wkbGeometry = WKBElement(buffer(pointGeom.wkb), srid)
        geomColumn = cls.geometryColumn() if geomColumn is None else geomColumn
        return func.ST_Intersects(geomColumn, wkbGeometry)

    """
    Returns a slqalchemy.sql.functions.Function
    Use it as a point filter to determine if a geometry should be returned (True or False)
    :params planGeom: A sqlAlchemy Column representing a postgis geometry (Must be a triangle)
    :params point: A list of dim 3 representing one point [X, Y, Z]
    """
    @classmethod
    def interpolateHeightOnPlane(cls, point, geomColumn=None, srid=4326):
        pointGeom = Point(point)
        wkbGeometry = WKBElement(buffer(pointGeom.wkb), srid)
        geomColumn = cls.geometryColumn() if geomColumn is None else geomColumn
        return func.ST_AsEWKB(_interpolate_height_on_plane(geomColumn, wkbGeometry))


"""
Returns a shapely.geometry.polygon.Polygon
:param bbox: A list of 4 cooridinates [minX, minY, maxX, maxY]
"""


def shapelyBBox(bbox):
    return box(*bbox)
