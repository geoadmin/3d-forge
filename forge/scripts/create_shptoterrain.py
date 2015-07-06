# -*- coding: utf-8 -*-

import os
from forge.models.terrain import TerrainTile
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology


basename = 'raron.flat.1'
directory = '.tmp'
extension = '.terrain'

curDir = os.getcwd()
filePathSource = '%s/forge/data/shapfile-features/%s.shp' % (curDir, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)

shapefile = ShpToGDALFeatures(shpFilePath=filePathSource)
features = shapefile.__read__()

terrainTopo = TerrainTopology(features=features)
terrainTopo.fromFeatures()
terrainFormat = TerrainTile()
terrainFormat.fromTerrainTopology(terrainTopo)
terrainFormat.toFile(filePathTarget)

# Display SwissCoordinates
terrainFormat.computeVerticesCoordinates(epsg=21781)
print terrainFormat
