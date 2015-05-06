# -*- coding: utf-8 -*-

import math


class BoundingSphere(object):

    def __init__(self, *args, **kwargs):

        self.center = map(float, kwargs.get('center', []))
        self.radius = float(kwargs.get('radius', 0))

    # Based on Ritter's algorithm
    def fromPoints(self, points):

        assert len(points) > 1, 'Your list of points must contain at least 2 points'
        randomPoint = points[0]

        # Find the point which has the largest distance from the initial random point.
        a = self.furthestPoint(randomPoint, points)
        # Search a point b in P, which has the largest distance from a.
        b = self.furthestPoint(a, points)

        # Initial center and radius
        self.center = self.getMidPoint(a, b)
        self.radius = self.distance(a, b)

        # Construct a new ball covering both point p and the previous ball
        for i in range(0, len(points)):
            point = points[i]
            distance = self.distance(self.center, point)
            # Point not included in the sphere
            if distance > self.radius:
                self.radius = newRadius = (self.radius + distance) / 2.0
                oldToNew = distance - newRadius
                self.center = [
                    (newRadius * self.center[0] + oldToNew * point[0]) / distance,
                    (newRadius * self.center[1] + oldToNew * point[1]) / distance,
                    (newRadius * self.center[2] + oldToNew * point[2]) / distance
                ]

    def getMidPoint(self, a, b):
        return [(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, (a[2] + b[2]) / 2.0]

    def furthestPoint(self, pointA, points):
        maxDistance = 0.0
        for i in range(0, len(points)):
            point = points[i]
            distance = self.distance(point, pointA)
            if maxDistance < distance:
                maxDistance = distance
                furthestPoint = point
        return furthestPoint

    def distanceSquared(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)

    def distance(self, p1, p2):
        return math.sqrt(self.distanceSquared(p1, p2))
