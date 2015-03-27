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
    return (z >> 1) if not z & 1 else -(z+1 >> 1)

def unpackEntry(entry):
    return unpack('<%s' %entry,  f.read(calcsize(entry)))[0]


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
  ['uVertexCount', 'H'], ## 2bytes
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
#etc...
#EdgeIndices16
#EdgeIndices32
#ExtensionHeader

with open('0.terrain', 'rb') as f:
    header = OrderedDict()
    for k, v in quantizedMeshHeader.iteritems():
        size = calcsize(v)
        header[k] = unpack('<%s' %v, f.read(size))[0]
    print 'Header: %s' %header

    vertexCount = unpackEntry(vertexData['vertexCount'])
    # 3 list of size count
    uVertexCount = []
    for i in range(0, vertexCount):
        uVertexCount.append(zigZagToNumber(
            unpackEntry(vertexData['uVertexCount'])
        ))
    vVertexCount = []
    for i in range(0, vertexCount):
        vVertexCount.append(zigZagToNumber(
            unpackEntry(vertexData['vVertexCount'])
        ))
    hVertexCount = []
    for i in range(0, vertexCount):
        hVertexCount.append(zigZagToNumber(
            unpackEntry(vertexData['heightVertexCount'])
        ))
    print len(uVertexCount)
    print 'uVertexCount: %s' %uVertexCount
    print len(vVertexCount)
    print 'vVertexCount: %s' %vVertexCount
    print len(hVertexCount)
    print 'hVertexCount: %s' %hVertexCount

    # Indexes
    triangleCount = unpackEntry(indexData16['triangleCount'])
    print 'triangleCount: %s' %triangleCount*3
    indexData = []
    if vertexCount > 65536:
        # unsigned int
        print 'Index data 32'
        for i in range(0, triangleCount*3):
            indexData.append(
                unpackEntry(indexData32['indices'])
            )
    else:
        # unsigned short
        print 'Index data 16'
        for i in range(0, triangleCount*3):
            indexData.append(
                unpackEntry(indexData16['indices'])
            )
    print 'indexData: %s' %indexData
