# -*- coding: utf-8 -*-

import math
import numpy as np
import forge.lib.cartesian3d as c3d


def centroid(a, b, c):
    return [sum((a[0], b[0], c[0])) / 3,
            sum((a[1], b[1], c[1])) / 3,
            sum([a[2], b[2], c[2]]) / 3]


# Based the vectors defining the plan
def triangleArea(a, b):
    i = math.pow(a[1] * b[2] - a[2] * b[1], 2)
    j = math.pow(a[2] * b[0] - a[0] * b[2], 2)
    k = math.pow(a[0] * b[1] - a[1] * b[0], 2)
    return 0.5 * math.sqrt(i + j + k)


# Inspired by
# https://github.com/AnalyticalGraphicsInc/cesium/wiki/Geometry-and-Appearances
# https://github.com/AnalyticalGraphicsInc/cesium/blob/master/
#     Source/Core/GeometryPipeline.js#L1071
def computeNormals(vertices, faces):
    numVertices = len(vertices)
    numFaces = len(faces)
    normalsPerFace = [None] * numFaces
    areasPerFace = [0.0] * numFaces
    normalsPerVertex = np.zeros(vertices.shape, dtype=vertices.dtype)

    for i in xrange(0, numFaces):
        face = faces[i]
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        ctrd = centroid(v0, v1, v2)

        v1A = c3d.subtract(v1, v0)
        v2A = c3d.subtract(v2, v0)
        normalA = np.cross(v1A, v2A)
        viewPointA = c3d.add(ctrd, normalA)

        v1B = c3d.subtract(v0, v1)
        v2B = c3d.subtract(v2, v1)
        normalB = np.cross(v1B, v2B)
        viewPointB = c3d.add(ctrd, normalB)

        area = triangleArea(v0, v1)
        areasPerFace[i] = area
        squaredDistanceA = c3d.magnitudeSquared(viewPointA)
        squaredDistanceB = c3d.magnitudeSquared(viewPointB)

        # Always take the furthest point
        if squaredDistanceA > squaredDistanceB:
            normalsPerFace[i] = normalA
        else:
            normalsPerFace[i] = normalB

    for i in xrange(0, numFaces):
        face = faces[i]
        for j in face:
            weightedNormal = [c * areasPerFace[i] for c in normalsPerFace[i]]
            normalsPerVertex[j] = c3d.add(
                normalsPerVertex[j], weightedNormal)

    for i in xrange(0, numVertices):
        normalsPerVertex[i] = c3d.normalize(normalsPerVertex[i])

    return normalsPerVertex


def listit(t):
    return list(map(listit, t)) if isinstance(t, (list, tuple)) else t


def getCoordsIndex(n, i):
    return i + 1 if n - 1 != i else 0


# Creates all the potential pairs of coords
def createCoordsPairs(l):
    coordsPairs = []
    for i in xrange(0, len(l)):
        coordsPairs.append([l[i], l[(i + 2) % len(l)]])
    return coordsPairs


def squaredDistances(coordsPairs):
    sDistances = []
    for coordsPair in coordsPairs:
        sDistances.append(c3d.distanceSquared(coordsPair[0], coordsPair[1]))
    return sDistances


def processRingCoordinates(ringCoordinates):
    nbPoints = len(ringCoordinates) - 1
    if nbPoints >= 4:
        # If this condition is not respected it means that we clipped
        # geometries that were not triangles
        if nbPoints not in (4, 5, 6, 7):
            raise Exception(
                'Error while processing the clipped geometries:'
                ' %s coords have been found' % nbPoints
            )
        return collapseIntoTriangles(ringCoordinates)
    else:
        return [ringCoordinates[0: len(ringCoordinates) - 1]]


def processRingsCoordinates(ringsCoordinates):
    rings = []
    for ring in ringsCoordinates:
        rings += processRingCoordinates(ring)
    return rings


def collapseIntoTriangles(ring):
    coords = listit(ring[0: len(ring) - 1])
    triangles = []
    while len(coords) > 3:
        # Create all possible pairs of coordinates
        coordsPairs = createCoordsPairs(coords)
        sDistances = squaredDistances(coordsPairs)
        index = sDistances.index(min(sDistances))
        i = getCoordsIndex(len(coords), index)
        triangle = coordsPairs[index] + [coords[i]]
        triangles.append(triangle)

        # Remove the converging point
        # As this point is not available to create a new triangle anymore
        convergingPoint = coords.index(coords[i])
        coords.pop(convergingPoint)

    return triangles + [coords]
