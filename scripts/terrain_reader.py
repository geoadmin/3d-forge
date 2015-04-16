# -*- coding: utf-8 -*-

## http://cesiumjs.org/data-and-assets/terrain/formats/quantized-mesh-1.0.html

from struct import *
from collections import OrderedDict


def numberToZigZag(n):
    """
    ZigZag-Encodes a number:
       -1 = 1
       -2 = 3
        0 = 0
        1 = 2
        2 = 4
    """
    return (n << 1) ^ (n >> 31)


def zigZagToNumber(z):
    """ Reverses ZigZag encoding """
    return (z >> 1) ^ (-(z & 1))
    #return (z >> 1) if not z & 1 else -(z+1 >> 1)


def unpackEntry(f, entry):
    return unpack('<%s' %entry,  f.read(calcsize(entry)))[0]


def unpackIndices(f, vertexCount, indicesCount, indices16, indices32):
    def createIndices(indicesCount, indicesType):
        indices = []
        for i in range(0, indicesCount):
            indices.append(
                unpackEntry(f, indicesType)
            )
        return indices

    if vertexCount > 65536:
        return createIndices(indicesCount, indices32)
    else:
        return createIndices(indicesCount, indices16)


def decodeIndices(indices):
    highest = 0
    for i in range(0, len(indices)):
        code = indices[i]
        indices[i] = highest - code
        if code == 0:
            highest += 1
    return indices


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

#ExtensionHeader

with open('0.terrain', 'rb') as f:
    header = OrderedDict()
    for k, v in quantizedMeshHeader.iteritems():
        size = calcsize(v)
        header[k] = unpack('<%s' %v, f.read(size))[0]
    print 'Header: %s' %header

    vertexCount = unpackEntry(f, vertexData['vertexCount'])
    # 3 list of size count
    uVertex = []
    for i in range(0, vertexCount):
        uVertex.append(zigZagToNumber(
            unpackEntry(f, vertexData['uVertexCount'])
        ))
    vVertex = []
    for i in range(0, vertexCount):
        vVertex.append(zigZagToNumber(
            unpackEntry(f, vertexData['vVertexCount'])
        ))
    hVertex = []
    for i in range(0, vertexCount):
        hVertex.append(zigZagToNumber(
            unpackEntry(f, vertexData['heightVertexCount'])
        ))
    print 'uVertex: %s' %uVertex
    print 'vVertex: %s' %vVertex
    print 'hVertex: %s' %hVertex

    # Indexes
    triangleCount = unpackEntry(f, indexData16['triangleCount'])
    indexData = unpackIndices(
        f, vertexCount, triangleCount*3, indexData16['indices'], indexData32['indices']
    )
    indexData = decodeIndices(indexData)
    print 'indexData: %s' %indexData

    # Read padding? Apparently we already reach the end the file at the moment

    # Edges (vertices on the edge of the tile) indices
    westIndicesCount = unpackEntry(f, EdgeIndices16['westVertexCount'])
    westIndices = unpackIndices(
        f, vertexCount, westIndicesCount, EdgeIndices16['westIndices'], EdgeIndices32['westIndices']
    )
    southIndicesCount = unpackEntry(f, EdgeIndices16['southVertexCount'])
    southIndices = unpackIndices(
        f, vertexCount, southIndicesCount, EdgeIndices16['southIndices'], EdgeIndices32['southIndices']
    )
    eastIndicesCount = unpackEntry(f, EdgeIndices16['eastVertexCount'])
    eastIndices = unpackIndices(
        f, vertexCount, eastIndicesCount, EdgeIndices16['eastIndices'], EdgeIndices32['eastIndices']
    )
    northIndicesCount = unpackEntry(f, EdgeIndices16['northVertexCount'])
    northIndices = unpackIndices(
        f, vertexCount, northIndicesCount, EdgeIndices16['northIndices'], EdgeIndices32['northIndices']
    )

    print 'westIndicesCount: %s' %westIndicesCount
    print 'westIndices: %s' %westIndices
    print 'southIndicesCount: %s' %southIndicesCount
    print 'southIndices: %s' %southIndices
    print 'eastIndicesCount: %s' %eastIndicesCount
    print 'eastIndices: %s' %eastIndices
    print 'northIndicesCount: %s' %northIndicesCount
    print 'northIndices: %s' %northIndices

    data = f.read(1)
    if not data:
        print 'end of file'
