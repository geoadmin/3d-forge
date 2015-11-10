# -*- coding: utf-8 -*-

from forge.terrain import TerrainTile
from forge.lib.global_geodetic import GlobalGeodetic


ter = TerrainTile()
path = 'forge/data/quantized-mesh/'
basename = '9_533_383'
extension = '.terrain'
fullPath = '%s%s%s' % (path, basename, extension)
geodetic = GlobalGeodetic(True)
zxy = basename.split('_')
bounds = geodetic.TileBounds(float(zxy[1]), float(zxy[2]), float(zxy[0]))

ter.fromFile(fullPath, bounds[1], bounds[3], bounds[0], bounds[2])
ter.computeVerticesCoordinates(epsg=21781)
print ter
