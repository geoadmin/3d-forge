# -*- coding: utf-8 -*-

import cStringIO
from forge.lib.helpers import gzipFileObject
from forge.lib.boto_conn import getBucket, writeToS3

bucket = getBucket()
layerJSONPath = '.tmp/layer.json'

with open(layerJSONPath) as f:
    fileObj = cStringIO.StringIO()
    fileObj.write(f.read())
    fileObj = gzipFileObject(fileObj)
    writeToS3(bucket, 'layer.json', fileObj, 'DB Scan', 'application/json')
