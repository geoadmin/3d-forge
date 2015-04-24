# -*- coding: utf-8 -*-

from struct import unpack, calcsize
from collections import OrderedDict
from forge.lib.helpers import zigZagToNumber
from forge.lib.decoders import unpackEntry, unpackIndices, decodeIndices
from forge.models.terrain import *


with open('forge/data/quantized-mesh/0.terrain', 'rb') as f:
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
