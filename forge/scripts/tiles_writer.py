# -*- coding: utf-8 -*-

import os
import time
import datetime
from boto.s3.key import Key
from forge.models.terrain import TerrainTile
from forge.lib.loaders import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology
from forge.lib.helpers import gzippedFileContent
from forge.lib.boto_conn import getBucket


def writeToS3(b, path, content, contentType='application/octet-stream'):
    headers = {'Content-Type': contentType}
    k = Key(b)
    k.key = path
    headers['Content-Encoding'] = 'gzip'
    k.set_contents_from_file(content, headers=headers)

basePath = '/var/local/cartoweb/tmp/3dpoc/swissalti3d/Interlaken_Pyr17/'
tempFolder = '.tmp/'
extension = '.terrain'

i = 0
t0 = time.time()
getShapefiles = lambda x: x.endswith('.shp')
shapefilesNames = filter(getShapefiles, os.listdir(basePath))
bucket = getBucket()

for f in shapefilesNames:
    filePathSource = basePath + f
    tempFileTarget = '%stempfile%s' % (tempFolder, extension)
    shapefile = ShpToGDALFeatures(shpFilePath=filePathSource)
    features = shapefile.__read__()
    terrainTopo = TerrainTopology(features=features)
    terrainTopo.fromFeatures()
    terrainFormat = TerrainTile()
    terrainFormat.fromTerrainTopology(terrainTopo)
    terrainFormat.toFile(tempFileTarget)
    compressedContent = gzippedFileContent(tempFileTarget)

    # Hardcoded scheme because we don't have any separators in the names
    # for now
    keyPath = f[1:3] + '/' + f[3:9] + '/' + f[9:14] + extension
    print 'Writing %s to S3' % keyPath
    writeToS3(bucket, keyPath, compressedContent)
    os.remove(tempFileTarget)
    i += 1
    t1 = time.time()
    ti = t1 - t0
    print 'It took %s secs to write %s/%s tiles' % (str(datetime.timedelta(seconds=ti)), i, len(shapefilesNames))
