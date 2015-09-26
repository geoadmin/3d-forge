# -*- coding: utf-8 -*-

import json
from forge.lib.boto_conn import getBucket, writeLayerJson

bucket = getBucket()
writeLayerJson(bucket, '.tmp/layerjson_old.json')

