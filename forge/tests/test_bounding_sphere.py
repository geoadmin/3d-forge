# -*- coding: utf-8 -*-

import unittest
from decimal import Decimal
from forge.lib.bounding_sphere import BoundingSphere


class TestBoundingSphere(unittest.TestCase):

    def testBoundingSphereAssign(self):
        center = [1, 3, 12]
        radius = 8
        sphere = BoundingSphere(center=center, radius=radius)
        self.failUnless(sphere.center[0] == 1.0)
        self.failUnless(sphere.center[1] == 3.0)
        self.failUnless(sphere.center[2] == 12.0)
        self.failUnless(sphere.radius == 8.0)

    def testBoundingSphereFromPoints(self):
        sphere = BoundingSphere()
        self.failUnless(len(sphere.center) == 0)
        self.failUnless(sphere.radius == 0.0)
        self.failUnless(sphere.minPoint[0] == Decimal('Infinity'))
        self.failUnless(sphere.maxPoint[1] == Decimal('-Infinity'))

        points = [[1.1, 3.2, 4.9], [3.1, 1.0, 21.4], [9.1, 3.2, 2.0], [2.0, 4.0, 9.5]]
        sphere.fromPoints(points)
        self.failUnless(sphere.minPoint[0] != Decimal('Infinity'))
        self.failUnless(sphere.maxPoint[1] != Decimal('-Infinity'))

        for point in points:
            distance = sphere.distance(sphere.center, point)
            self.failUnless(distance <= sphere.radius)

        # Point outside the sphere
        pointOutside = [1000.0, 1000.0, 1000.0]
        distance = sphere.distance(sphere.center, pointOutside)
        self.failUnless(distance > sphere.radius)
