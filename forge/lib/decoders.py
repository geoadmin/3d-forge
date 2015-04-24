# -*- coding: utf-8 -*-

from struct import unpack, calcsize


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
