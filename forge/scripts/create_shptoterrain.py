# -*- coding: utf-8 -*-

import os
from forge.models.terrain import TerrainTile
from forge.lib.loaders import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology


basename = 'raron.flat.1'
directory = '.tmp'
extension = '.shp'

if os.path.isfile('%s/%s%s' % (directory, basename, extension)):
    raise IOError('File %s/%s%s already exists' % (directory, basename, extension))

curDir = os.getcwd()
shapefile = ShpToGDALFeatures(shpFilePath=curDir + '/forge/data/shapfile-features/' + basename + '.shp')
features = shapefile.__read__()
terrainTopo = TerrainTopology(features)
terrainTopo.create()
terrainFormat = TerrainTile()
terrainFormat.fromTerrainTopology(terrainTopo)
print terrainFormat
terrainFormat.toFile(directory + '/' + basename + '.terrain')
