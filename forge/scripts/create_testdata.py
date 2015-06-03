# -*- coding: utf-8 -*-

from forge.models.terrain import TerrainTile

basename = 'raron.flat.1'
directory = '.tmp'
extension = '.shp'

# Read terrain file
filePathSource = 'forge/data/quantized-mesh/%s.terrain' % basename
filePathTarget = '%s/%s%s' % (directory, basename, extension)
ter = TerrainTile()
ter.fromFile(filePathSource, 7.80938, 7.81773, 46.30261, 46.30799)
ter.toShapefile(filePathTarget)
print ter
