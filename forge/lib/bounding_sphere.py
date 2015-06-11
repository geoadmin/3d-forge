# -*- coding: utf-8 -*-

import math


class BoundingSphere(object):

    def __init__(self, *args, **kwargs):
        MAX = float('infinity')
        MIN = float('-infinity')
        self.center = map(float, kwargs.get('center', []))
        self.radius = float(kwargs.get('radius', 0))
        self.minPointX = [MAX, MAX, MAX]
        self.minPointY = [MAX, MAX, MAX]
        self.minPointZ = [MAX, MAX, MAX]
        self.maxPointX = [MIN, MIN, MIN]
        self.maxPointY = [MIN, MIN, MIN]
        self.maxPointZ = [MIN, MIN, MIN]

    # Based on Ritter's algorithm
    def fromPoints(self, points):

        if len(points) < 1:
            raise Exception('Your list of points must contain at least 2 points')

        nbPositions = len(points)
        for i in xrange(0, nbPositions):
            point = points[i]

            # Store the points containing the smallest and largest component
            # Used for the naive approach
            if point[0] < self.minPointX[0]:
                self.minPointX = point

            if point[1] < self.minPointY[1]:
                self.minPointY = point

            if point[2] < self.minPointZ[2]:
                self.minPointZ = point

            if point[0] > self.maxPointX[0]:
                self.maxPointX = point

            if point[1] > self.maxPointY[1]:
                self.maxPointY = point

            if point[2] > self.maxPointZ[2]:
                self.maxPointZ = point

        # Squared distance between each component min and max
        xSpan = self.magnitudeSquared(self.subtract(self.maxPointX, self.minPointX))
        ySpan = self.magnitudeSquared(self.subtract(self.maxPointY, self.minPointY))
        zSpan = self.magnitudeSquared(self.subtract(self.maxPointZ, self.minPointZ))

        diameter1 = self.minPointX
        diameter2 = self.maxPointX
        maxSpan = xSpan
        if ySpan > maxSpan:
            maxSpan = ySpan
            diameter1 = self.minPointY
            diameter2 = self.maxPointY
        if zSpan > maxSpan:
            maxSpan = zSpan
            diameter1 = self.minPointZ
            diameter2 = self.maxPointZ

        ritterCenter = [
            (diameter1[0] + diameter2[0]) * 0.5,
            (diameter1[1] + diameter2[1]) * 0.5,
            (diameter1[2] + diameter2[2]) * 0.5
        ]

        radiusSquared = self.magnitudeSquared(self.subtract(diameter2, ritterCenter))
        ritterRadius = math.sqrt(radiusSquared)

        # Initial center and radius (naive) get min and max box
        minBoxPt = [self.minPointX[0], self.minPointY[1], self.minPointZ[2]]
        maxBoxPt = [self.maxPointX[0], self.maxPointY[1], self.maxPointZ[2]]
        naiveCenter = self.multiplyByScalar(self.add(minBoxPt, maxBoxPt), 0.5)
        naiveRadius = 0.0

        for i in xrange(0, nbPositions):
            currentP = points[i]

            # Find the furthest point from the naive center to calculate the naive radius.
            r = self.magnitude(self.subtract(currentP, naiveCenter))
            if r > naiveRadius:
                naiveRadius = r

            # Make adjustments to the Ritter Sphere to include all points.
            oldCenterToPointSquared = self.magnitudeSquared(self.subtract(currentP, ritterCenter))
            if oldCenterToPointSquared > radiusSquared:
                oldCenterToPoint = math.sqrt(oldCenterToPointSquared)
                ritterRadius = (ritterRadius + oldCenterToPoint) * 0.5
                # Calculate center of new Ritter sphere
                oldToNew = oldCenterToPoint - ritterRadius
                ritterCenter = [
                    (ritterRadius * ritterCenter[0] + oldToNew * currentP[0]) / oldCenterToPoint,
                    (ritterRadius * ritterCenter[1] + oldToNew * currentP[1]) / oldCenterToPoint,
                    (ritterRadius * ritterCenter[2] + oldToNew * currentP[2]) / oldCenterToPoint,
                ]

        # Keep the naive sphere if smaller
        if naiveRadius < ritterRadius:
            self.radius = ritterRadius
            self.center = ritterCenter
        else:
            self.radius = naiveRadius
            self.center = naiveCenter

    def magnitudeSquared(self, p):
        return p[0] ** 2 + p[1] ** 2 + p[2] ** 2

    def magnitude(self, p):
        return math.sqrt(self.magnitudeSquared(p))

    def add(self, left, right):
        return [left[0] + right[0], left[1] + right[1], left[2] + right[2]]

    def subtract(self, left, right):
        return [left[0] - right[0], left[1] - right[1], left[2] - right[2]]

    def distanceSquared(self, p1, p2):
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2

    def distance(self, p1, p2):
        return math.sqrt(self.distanceSquared(p1, p2))

    def multiplyByScalar(self, p, scalar):
        return [p[0] * scalar, p[1] * scalar, p[2] * scalar]
