# -*- coding: utf-8 -*-

import os
from forge.lib.tiler import GlobalGeodeticTiler

basePath = '/var/local/cartoweb/tmp/3dpoc/'
# We already have level 0 and 1 (the whole globe)
foldersName = range(2, 18)
getShapefiles = lambda x: x.endswith('Merge.shp')

dataSourcePaths = []
for f in foldersName:
    path = '%s%s/' % (basePath, f)
    shapefilesName = filter(getShapefiles, os.listdir(path))
    dataSourcePaths.append('%s%s/%s' % (basePath, f, shapefilesName[0]))

minLon = 7.814408987957777
maxLon = 7.8720231243555085
minLat = 46.68040307776367
maxLat = 46.7345778113877

tiler = GlobalGeodeticTiler(minLon, maxLon, minLat, maxLat, 2, 17, dataSourcePaths)
tiler.createTiles()
