# -*- coding: utf-8 -*-

import os
from forge.models.terrain import TerrainTile
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.topology import TerrainTopology
from forge.lib.global_geodetic import GlobalGeodetic


basename = '7_133_98'
directory = '.tmp'
extension = '.terrain'

curDir = os.getcwd()
filePathSource = '%s/forge/data/shapefile-features/%s.shp' % (curDir, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)

shapefile = ShpToGDALFeatures(shpFilePath=filePathSource)
features = shapefile.__read__()

terrainTopo = TerrainTopology(features=features)
terrainTopo.fromFeatures()
terrainFormat = TerrainTile()

geodetic = GlobalGeodetic(True)
zxy = basename.split('_')
bounds = geodetic.TileBounds(float(zxy[1]), float(zxy[2]), float(zxy[0]))

terrainFormat.fromTerrainTopology(terrainTopo, bounds)
terrainFormat.toFile(filePathTarget)

# Display SwissCoordinates
terrainFormat.computeVerticesCoordinates(epsg=21781)
print terrainFormat
