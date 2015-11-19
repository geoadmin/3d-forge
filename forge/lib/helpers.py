# -*- coding: utf-8 -*-

from osgeo import osr, ogr
import requests
import os
import gzip
import sys
import time
import datetime
import cStringIO
from pyproj import Proj, transform


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


def createBBox(center, length):
    offset = length / 2
    xmin = center[0] - offset
    ymin = center[1] - offset
    xmax = center[0] + offset
    ymax = center[1] + offset
    return [xmin, ymin, xmax, ymax]


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


def error(msg, exitCode=1, usage=None):
    print('Error: %(msg)s.' % {'msg': msg})
    print('')
    if usage is not None:
        usage()
    sys.exit(exitCode)


def resourceExists(path, headers={}):
    try:
        r = requests.head(path, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise requests.exceptions.ConnectionError(e)
    return r.status_code == requests.codes.ok


def cleanup(filePath, extensions=['.shp', '.shx', '.prj', '.dbf']):
    if os.path.isfile(filePath):
        dirName = os.path.dirname(filePath)
        baseName = os.path.basename(filePath).split('.')[0]
        for ext in extensions:
            try:
                os.remove('%s/%s%s' % (dirName, baseName, ext))
            except OSError as e:
                raise OSError(e)

# Approximation only, arc must be provided in degrees


def degreesToMeters(arc):
    projWGS84 = Proj(proj='latlong', datum='WGS84')
    projLV03 = Proj(init='epsg:21781')
    chCenterWGS84 = [8.3, 46.85]
    p1 = transform(projWGS84, projLV03, *chCenterWGS84)
    p2 = transform(projWGS84, projLV03, chCenterWGS84[0] + arc, chCenterWGS84[1])
    return p2[0] - p1[0]


class Bulk:

    def __init__(self, rows=None):
        self.rows = list() if rows is None else rows
        self.n = len(self.rows)

    def add(self, row):
        self.n = self.n + 1
        self.rows.append(row)

    def commit(self, model, session):
        if self.n > 0:
            session.bulk_insert_mappings(
                model,
                self.rows
            )
            session.commit()
            self.n = 0
            self.rows = list()


class BulkInsert:

    NO_LIMIT = float('inf')

    def __init__(self, model, session, withAutoCommit=None):
        self.model = model
        self.session = session
        self.autoCommit = withAutoCommit if withAutoCommit is not None else \
            BulkInsert.NO_LIMIT
        self.bulk = Bulk()

    def add(self, row):
        if self.bulk.n < self.autoCommit:
            self.bulk.add(row)
        else:
            self.bulk.commit(self.model, self.session)
            self.bulk = Bulk([row])

    def addN(self, rows):
        for row in rows:
            self.add(row)

    def commit(self):
        self.bulk.commit(self.model, self.session)
        self.bulk = Bulk([])
