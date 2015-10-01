# -*- coding: utf-8 -*-

from forge.terrain import TerrainTile

ter = TerrainTile()
# ter.fromFile('forge/data/quantized-mesh/0.terrain')
ter.fromFile('forge/data/quantized-mesh/raron.flat.1.terrain', 7.80938, 7.81773, 46.30261, 46.30799)
# ter.fromFile('forge/data/quantized-mesh/goms.mountains.1.terrain')
ter.computeVerticesCoordinates(epsg=21781)
print ter
