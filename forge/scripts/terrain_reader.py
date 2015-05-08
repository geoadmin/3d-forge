# -*- coding: utf-8 -*-

from forge.models.terrain import TerrainTile

ter = TerrainTile()

#ter.fromFile('forge/data/quantized-mesh/0.terrain')
#ter.fromFile('forge/data/quantized-mesh/raron.flat.1.terrain')
ter.fromFile('forge/data/quantized-mesh/goms.mountains.1.terrain')
print ter
