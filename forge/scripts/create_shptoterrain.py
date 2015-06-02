# -*- coding: utf-8 -*-

import os
from forge.models.terrain import TerrainTile
from forge.lib.loaders import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology


basename = 'raron.flat.1'
directory = '.tmp'
extension = '.terrain'

curDir = os.getcwd()
filePathSource = '%s/forge/data/shapfile-features/%s.shp' % (curDir, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)

shapefile = ShpToGDALFeatures(shpFilePath=filePathSource)
features = shapefile.__read__()

terrainTopo = TerrainTopology(features)
terrainTopo.create()
terrainFormat = TerrainTile()
terrainFormat.fromTerrainTopology(terrainTopo)
print terrainFormat

terrainFormat.toFile(filePathTarget)
