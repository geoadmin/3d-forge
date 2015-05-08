# -*- coding: utf-8 -*-

from osgeo import osr, ogr


def numberToZigZag(n):
    """
    ZigZag-Encodes a number:
       -1 = 1
       -2 = 3
        0 = 0
        1 = 2
        2 = 4
    """
    return (n << 1) ^ (n >> 31)


def zigZagToNumber(z):
    """ Reverses ZigZag encoding """
    return (z >> 1) ^ (-(z & 1))
    # return (z >> 1) if not z & 1 else -(z+1 >> 1)


def transformCoordinate(wkt, srid_from, srid_to):
    srid_in = osr.SpatialReference()
    srid_in.ImportFromEPSG(srid_from)
    srid_out = osr.SpatialReference()
    srid_out.ImportFromEPSG(srid_to)
    geom = ogr.CreateGeometryFromWkt(wkt)
    geom.AssignSpatialReference(srid_in)
    geom.TransformTo(srid_out)
    return geom
