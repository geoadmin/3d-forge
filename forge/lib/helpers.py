# -*- coding: utf-8 -*-

from osgeo import osr, ogr
import gzip
import time
import datetime
import cStringIO


def zigZagEncode(n):
    """
    ZigZag-Encodes a number:
       -1 = 1
       -2 = 3
        0 = 0
        1 = 2
        2 = 4
    """
    return (n << 1) ^ (n >> 31)


def zigZagDecode(z):
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


def gzipFileContent(filePath):
    content = open(filePath)
    compressed = cStringIO.StringIO()
    gz = gzip.GzipFile(fileobj=compressed, mode='w')
    gz.writelines(content)
    gz.close()
    compressed.seek(0)
    content.close()
    return compressed


def gzipFileObject(data):
    compressed = cStringIO.StringIO()
    gz = gzip.GzipFile(fileobj=compressed, mode='w', compresslevel=5)
    gz.write(data.getvalue())
    gz.close()
    compressed.seek(0)
    return compressed


def isShapefile(filePath):
    return filePath.endswith('.shp')


def timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
