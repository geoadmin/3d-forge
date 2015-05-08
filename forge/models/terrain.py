# -*- coding: utf-8 -*-

from struct import unpack, calcsize
from collections import OrderedDict
from forge.lib.helpers import zigZagToNumber
from forge.lib.decoders import unpackEntry, unpackIndices, decodeIndices


# http://cesiumjs.org/data-and-assets/terrain/formats/quantized-mesh-1.0.html
class Meta:
    quantizedMeshHeader = OrderedDict([
        ['centerX', 'd'],  # 8bytes
        ['centerY', 'd'],
        ['centerZ', 'd'],
        ['minimumHeight', 'f'],  # 4bytes
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
        ['vertexCount', 'I'],  # 4bytes -> determines the size of the 3 following arrays
        ['uVertexCount', 'H'],  # 2bytes, unsigned short
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


class Terrain:

    def __init__(self):
        self.header = OrderedDict()
        for k, v in Meta.quantizedMeshHeader.iteritems():
            self.header[k] = 0.0
        self.u = []
        self.v = []
        self.h = []
        self.indices = []
        self.westI = []
        self.southI = []
        self.eastI = []
        self.northI = []

    def __str__(self):
        str = 'Header: %s' % self.header
        str += '\nVertexCount: %s' % len(self.u)
        str += '\nuVertex: %s' % self.u
        str += '\nvVertex: %s' % self.v
        str += '\nhVertex: %s' % self.h
        str += '\nindexData: %s' % self.indices
        str += '\nwestIndicesCount: %s' % len(self.westI)
        str += '\nwestIndices: %s' % self.westI
        str += '\nsouthIndicesCount: %s' % len(self.southI)
        str += '\nsouthIndices: %s' % self.southI
        str += '\neastIndicesCount: %s' % len(self.eastI)
        str += '\neastIndices: %s' % self.eastI
        str += '\nnorthIndicesCount: %s' % len(self.northI)
        str += '\nnorthIndices: %s' % self.northI
        return str

    def fromFile(self, filename):
        self.__init__()
        with open(filename, 'rb') as f:
            for k, v in Meta.quantizedMeshHeader.iteritems():
                size = calcsize(v)
                self.header[k] = unpack('<%s' % v, f.read(size))[0]

            vertexCount = unpackEntry(f, Meta.vertexData['vertexCount'])
            for i in range(0, vertexCount):
                self.u.append(zigZagToNumber(
                    unpackEntry(f, Meta.vertexData['uVertexCount'])
                ))
            for i in range(0, vertexCount):
                self.v.append(zigZagToNumber(
                    unpackEntry(f, Meta.vertexData['vVertexCount'])
                ))
            for i in range(0, vertexCount):
                self.h.append(zigZagToNumber(
                    unpackEntry(f, Meta.vertexData['heightVertexCount'])
                ))
            # Indexes
            triangleCount = unpackEntry(f, Meta.indexData16['triangleCount'])
            self.indices = unpackIndices(
                f, vertexCount, triangleCount * 3, Meta.indexData16['indices'], Meta.indexData32['indices']
            )
            self.indices = decodeIndices(self.indices)

            # Read padding? Apparently we already reach the end the file at the moment

            # Edges (vertices on the edge of the tile) indices
            westIndicesCount = unpackEntry(f, Meta.EdgeIndices16['westVertexCount'])
            self.westI = unpackIndices(
                f, vertexCount, westIndicesCount, Meta.EdgeIndices16['westIndices'], Meta.EdgeIndices32['westIndices']
            )
            southIndicesCount = unpackEntry(f, Meta.EdgeIndices16['southVertexCount'])
            self.southI = unpackIndices(
                f, vertexCount, southIndicesCount, Meta.EdgeIndices16['southIndices'], Meta.EdgeIndices32['southIndices']
            )
            eastIndicesCount = unpackEntry(f, Meta.EdgeIndices16['eastVertexCount'])
            self.eastI = unpackIndices(
                f, vertexCount, eastIndicesCount, Meta.EdgeIndices16['eastIndices'], Meta.EdgeIndices32['eastIndices']
            )
            northIndicesCount = unpackEntry(f, Meta.EdgeIndices16['northVertexCount'])
            self.northI = unpackIndices(
                f, vertexCount, northIndicesCount, Meta.EdgeIndices16['northIndices'], Meta.EdgeIndices32['northIndices']
            )

            data = f.read(1)
            if data:
                raise Exception('Should have reached end of file, but didn\'t')
