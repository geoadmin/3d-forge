# -*- coding: utf-8 -*-

import os
from forge.models.terrain import TerrainTile
from forge.lib.loaders import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology


basename = 'raron.flat.1'
directory = '.tmp'

try:
    os.makedirs(directory)
except:
    print 'Directory %s already exists' % directory

curDir = os.getcwd()
shapefile = ShpToGDALFeatures(shpFilePath=curDir + '/forge/data/shapfile-features/' + basename + '.shp')
features = shapefile.__read__()
terrainTopo = TerrainTopology(features)
terrainTopo.create()
terrainFormat = TerrainTile()
terrainFormat.fromTerrainTopology(terrainTopo)
print terrainFormat
terrainFormat.toFile(directory + '/' + basename + '.terrain')
