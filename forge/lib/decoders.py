# -*- coding: utf-8 -*-

from struct import pack, unpack, calcsize


def packEntry(type, value):
    return pack('<%s' % type, value)


def unpackEntry(f, entry):
    return unpack('<%s' % entry, f.read(calcsize(entry)))[0]


def packIndices(f, type, indices):
    for i in indices:
        f.write(packEntry(type, i))


def unpackIndices(f, indicesCount, indicesType):
    indices = []
    for i in xrange(0, indicesCount):
        indices.append(
            unpackEntry(f, indicesType)
        )
    return indices


def decodeIndices(indices):
    out = []
    highest = 0
    for i in indices:
        out.append(highest - i)
        if i == 0:
            highest += 1
    return out


def encodeIndices(indices):
    out = []
    highest = 0
    for i in indices:
        code = highest - i
        out.append(code)
        if code == 0:
            highest += 1
    return out
