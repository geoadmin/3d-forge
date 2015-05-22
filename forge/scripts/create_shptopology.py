# -*- coding: utf-8 -*-

import os
from forge.lib.loaders import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology

curDir = os.getcwd()
shapefile = ShpToGDALFeatures(shpFilePath=curDir + '/forge/data/shapfile-features/raron.flat.1.shp')
features = shapefile.__read__()
terrainTopo = TerrainTopology(features)
terrainTopo.create()
print terrainTopo
