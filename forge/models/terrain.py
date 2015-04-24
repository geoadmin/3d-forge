# -*- coding: utf-8 -*-

from collections import OrderedDict


## http://cesiumjs.org/data-and-assets/terrain/formats/quantized-mesh-1.0.html
quantizedMeshHeader = OrderedDict([
  ['centerX', 'd'], ## 8bytes
  ['centerY', 'd'],
  ['centerZ', 'd'],
  ['minimumHeight', 'f'], ## 4bytes
  ['maximumHeight', 'f'],
  ['boundingSphereCenterX', 'd'],
  ['boundingSphereCenterY', 'd'],
  ['boundingSphereCenterZ', 'd'],
  ['boundingSphereRadius', 'd'],
  ['horizonOcclusionPointX', 'd'],
  ['horizonOcclusionPointY', 'd'],
  ['horizonOcclusionPointZ', 'd']
])

vertexData = OrderedDict([
  ['vertexCount', 'I'], ## 4bytes -> determines the size of the 3 following arrays
  ['uVertexCount', 'H'], ## 2bytes, unsigned short
  ['vVertexCount', 'H'],
  ['heightVertexCount', 'H']
])

indexData16 = OrderedDict([
  ['triangleCount', 'I'],
  ['indices', 'H']
])
indexData32 = OrderedDict([
  ['triangleCount', 'I'],
  ['indices', 'I']
])

EdgeIndices16 = OrderedDict([
  ['westVertexCount', 'I'],
  ['westIndices', 'H'],
  ['southVertexCount', 'I'],
  ['southIndices', 'H'],
  ['eastVertexCount', 'I'],
  ['eastIndices', 'H'],
  ['northVertexCount', 'I'],
  ['northIndices', 'H']
])
EdgeIndices32 = OrderedDict([
  ['westVertexCount', 'I'],
  ['westIndices', 'I'],
  ['southVertexCount', 'I'],
  ['southIndices', 'I'],
  ['eastVertexCount', 'I'],
  ['eastIndices', 'I'],
  ['northVertexCount', 'I'],
  ['northIndices', 'I']
])
