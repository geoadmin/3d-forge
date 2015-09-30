# -*- coding: utf-8 -*-

from forge.lib.boto_conn import getBucket, writeLayerJson

bucket = getBucket()
writeLayerJson(bucket, 'forge/data/json-conf/layer.json')
