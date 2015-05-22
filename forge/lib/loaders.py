# -*- coding: utf-8 -*-

import re
from osgeo import ogr


class ShpToGDALFeatures(object):

    def __init__(self, shpFilePath=None):
        if shpFilePath is None:
            raise Exception('No shapefile path provided')
        if re.search(r'(\.shp)$', shpFilePath) is None:
            raise TypeError('Only shapefiles are supported. Provided path %s' % shpFilePath)
        self.shpFilePath = shpFilePath

    # Returns a list of GDAL Features
    def __read__(self):
        drvName = 'ESRI Shapefile'
        drv = ogr.GetDriverByName(drvName)
        # 0 refers to read-only
        dataSource = drv.Open(self.shpFilesPath, 0)
        if dataSource is None:
            raise IOError('Could not open %s.' % self.shpFilePath)
        print 'Opening shapefile...'
        layer = dataSource.GetLayer()
        features = [feature for feature in layer]
        if len(features) == 0:
            raise Exception('Empty shapefile')

        geometryType = features[0].GetGeometryRef().GetGeometryName()
        if geometryType != 'POLYGON':
            raise TypeError('Unsupported input geometry type: %s' % geometryType)
        return features
