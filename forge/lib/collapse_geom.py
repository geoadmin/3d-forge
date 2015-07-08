# -*- coding: utf-8 -*-

import forge.lib.cartesian3d as c3d


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


def processRingsCoordinates(ringsCoordinates):
    rings = []
    for ring in ringsCoordinates:
        nbPoints = len(ring) - 1
        if nbPoints >= 4:
            # If this condition is not respected it means that we clipped
            # geometries that were not triangles
            if nbPoints not in (4, 5, 6, 7):
                raise Exception('Error while processing the clipped geometries: %s coords have been found' % nbPoints)
            triangles = collapseIntoTriangles(ring)
            rings += triangles
        else:
            rings += [ring[0: len(ring) - 1]]
    return rings


def collapseIntoTriangles(ring):
    coords = listit(ring[0: len(ring) - 1])
    triangles = []
    while len(coords) > 3:
        # Create all possible pairs of coordinates
        coordsPairs = createCoordsPairs(coords)
        sDistances = squaredDistances(coordsPairs)

        index = sDistances.index(max(sDistances))
        i = getCoordsIndex(len(coords), index)
        triangle = coordsPairs[index] + [coords[i]]
        triangles.append(triangle)

        # Remove the converging point
        # As this point is not available to create a new triangle anymore
        convergingPoint = coords.index(coords[i])
        coords.pop(convergingPoint)

    return triangles + [coords]
