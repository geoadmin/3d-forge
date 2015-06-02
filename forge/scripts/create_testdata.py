# -*- coding: utf-8 -*-

import os
import osgeo.ogr as ogr
import osgeo.osr as osr
from forge.models.terrain import TerrainTile

basename = 'raron.flat.1'
directory = '.tmp'
extension = '.shp'

# Prepare writing of shapefile
drv = ogr.GetDriverByName('ESRI Shapefile')
if os.path.isfile('%s/%s%s' % (directory, basename, extension)):
    raise IOError('File %s/%s%s already exists' % (directory, basename, extension))
dataSource = drv.CreateDataSource('%s/%s%s' % (directory, basename, extension))
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
layer = dataSource.CreateLayer(basename, srs, ogr.wkbPolygon25D)


# Read terrain file
ter = TerrainTile()
ter.fromFile('forge/data/quantized-mesh/' + basename + '.terrain', 7.80938, 7.81773, 46.30261, 46.30799)
ter._updateCoords()

for i in range(0, len(ter.indices), 3):
    # triangle is i, i+1 and i+2
    feature = ogr.Feature(layer.GetLayerDefn())
    coords = (ter._longs[ter.indices[i]], ter._lats[ter.indices[i]], ter._heights[ter.indices[i]],
              ter._longs[ter.indices[i + 1]], ter._lats[ter.indices[i + 1]], ter._heights[ter.indices[i + 1]],
              ter._longs[ter.indices[i + 2]], ter._lats[ter.indices[i + 2]], ter._heights[ter.indices[i + 2]],
              ter._longs[ter.indices[i]], ter._lats[ter.indices[i]], ter._heights[ter.indices[i]])
    wkt = 'POLYGON ((%f %f %f, %f %f %f, %f %f %f, %f %f %f))' % coords
    polygon = ogr.CreateGeometryFromWkt(wkt)
    feature.SetGeometry(polygon)
    layer.CreateFeature(feature)
    feature.Destroy()

dataSource.Destroy()

from forge.lib.loaders import ShpToGDALFeatures

shapefile = ShpToGDALFeatures(shpFilePath='%s/%s%s' % (directory, basename, extension))

features = shapefile.__read__()

for f in features:
    print f.GetGeometryRef().ExportToWkt()
