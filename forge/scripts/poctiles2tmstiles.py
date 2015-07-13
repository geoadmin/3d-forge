# -*- coding: utf-8 -*-

import sys
import gzip
import os
from urllib2 import urlopen
from textwrap import dedent

from forge.lib.global_geodetic import GlobalGeodetic
from forge.lib.helpers import error
from forge.models.terrain import TerrainTile
from forge.lib.helpers import gzipFileObject
from forge.lib.boto_conn import getBucket, writeToS3
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology


poc_base_url = "http://ec2-54-220-242-89.eu-west-1.compute.amazonaws.com/stk-terrain/tilesets/swisseudem/tiles/"
temp_file_name = "tmp/poc.terrain"
gzip_file_name = temp_file_name + ".gzip"
tms_file_name = "tmp/tms.terrain"
shape_file_name = "tmp/shape.shp"
tms_from_shape_file_name = "tmp/tms.from.shape.terrain"


def usage():
    print(dedent('''\
        Usage: venv/bin/python forge/script/poctiles2tmstiles.py <file>')

        The <file> contains tiles to transform in the form /z/x/y

        Could/should be adapted to define range easier, and not via file.

        Script will
            1) get given tile from poc url
            2) read tile with TerrainTile class (fromFile function)
            3) write tile to shapefile
            4) Create tile from shapefile
            4) Write tile to our S3 bucket under given addres /z/x/y
    '''))


def main():
    if len(sys.argv) != 2:
        error("Please specify a file.", 4, usage=usage)
    ffile = sys.argv[1]
    bucket = getBucket()
    g = GlobalGeodetic(tmscompatible=True)
    if not os.path.isdir('tmp'):
        os.mkdir('tmp')
    with open(ffile) as f:
        for line in f:
            line = line.rstrip()
            if len(line) > 2:
                req = None
                # Getting Tilebounds with GlobalGeodetic
                splits = map(int, line.split('/'))
                tilebounds = g.TileBounds(splits[1], splits[2], splits[0])
                try:
                    url = poc_base_url + line + ".terrain?v=2.0.0"
                    req = urlopen(url)
                    with open(gzip_file_name, 'wb') as fp:
                        fp.write(req.read())
                    ff = gzip.open(gzip_file_name)
                    with open(temp_file_name, 'wb') as fp:
                        fp.write(ff.read())

                    ter = TerrainTile()
                    ter.fromFile(temp_file_name, tilebounds[0], tilebounds[2], tilebounds[1], tilebounds[3])

                    if os.path.isfile(tms_file_name):
                        os.remove(tms_file_name)

                    if os.path.isfile(shape_file_name):
                        os.remove(shape_file_name)

                    if os.path.isfile(tms_from_shape_file_name):
                        os.remove(tms_from_shape_file_name)

                    ter.toFile(tms_file_name)
                    ter.toShapefile(shape_file_name)

                    shapefile = ShpToGDALFeatures(shpFilePath=shape_file_name)
                    features = shapefile.__read__()
                    topology = TerrainTopology(features=features)
                    topology.fromFeatures()

                    terFromPoc = TerrainTile()
                    terFromPoc.fromFile(tms_file_name, tilebounds[0], tilebounds[2], tilebounds[1], tilebounds[3])
                    print tilebounds[0], tilebounds[2], tilebounds[1], tilebounds[3]

                    terFromShape = TerrainTile()
                    terFromShape.fromTerrainTopology(topology)
                    # replace header with original
                    terFromShape.toFile(tms_from_shape_file_name)

                    # Use this to select what is written to s3
                    # ter2 = terFromPoc
                    ter2 = terFromShape
                    ter2.header['horizonOcclusionPointX'] = ter.header['horizonOcclusionPointX']
                    ter2.header['horizonOcclusionPointY'] = ter.header['horizonOcclusionPointY']
                    ter2.header['horizonOcclusionPointZ'] = ter.header['horizonOcclusionPointZ']

                    fileObject = ter2.toStringIO()
                    compressedFile = gzipFileObject(fileObject)

                    bucketKey = line + '.terrain'
                    print 'Uploading %s to S3' % bucketKey
                    writeToS3(bucket, bucketKey, compressedFile)

                except Exception as e:
                    print "error with " + line + " " + str(e)
                finally:
                    if req:
                        req.close()
    return 0


if __name__ == '__main__':
    main()
