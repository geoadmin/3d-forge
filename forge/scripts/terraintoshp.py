# -*- coding: utf-8 -*-

from forge.terrain import TerrainTile
from forge.lib.global_geodetic import GlobalGeodetic

basename = '7_133_98'
directory = '.tmp'
extension = '.shp'

# Read terrain file
filePathSource = 'forge/data/quantized-mesh/%s.terrain' % basename
filePathTarget = '%s/%s%s' % (directory, basename, extension)
ter = TerrainTile()

geodetic = GlobalGeodetic(True)
zxy = basename.split('_')
bounds = geodetic.TileBounds(float(zxy[1]), float(zxy[2]), float(zxy[0]))

print bounds
ter.fromFile(filePathSource, bounds[0], bounds[2], bounds[1], bounds[3])
ter.toShapefile(filePathTarget)

# In order to display swiss coordinates
ter.computeVerticesCoordinates(epsg=21781)
print ter
