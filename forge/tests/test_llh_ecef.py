# -*- coding: utf-8 -*-

import unittest
from forge.lib.llh_ecef import LLH2ECEF, ECEF2LLH

# Conversion reference
# http://www.oc.nps.edu/oc2902w/coord/llhxyz.htm
class TestLLFECEF(unittest.TestCase):

    def testLLFToECEF(self):
        (lat, lon, alt) = (0, 0, 0)
        (x, y, z) = LLH2ECEF(lat, lon, alt)
        self.failUnless(x == 6378137.0)
        self.failUnless(y == 0.0)
        self.failUnless(z == 0.0)

        # Swiss like lat/lon/alt
        (lat, lon, alt) = (8.23, 4.03, 707)
        (x, y, z) = LLH2ECEF(lat, lon, alt)
        self.failUnless(round(x) == 6297973.0)
        self.failUnless(round(y) == 443711.0)
        self.failUnless(round(z) == 907064.0)

    def testECEF2LLH(self):
        (x, y, z) = (0, 0, 6358000)
        (lat, lon, alt) = ECEF2LLH(x, y, z)
        self.failUnless(lat == 90.0)
        self.failUnless(lon == 0.0)
        self.failUnless(round(z) == 6358000.0)

        # Swiss like x/y/z
        (x, y, z) = (6297973, 443711, 907064)
        (lat, lon, alt) = ECEF2LLH(x, y, z)
        self.failUnless(round(lat, 2) == 8.23)
        self.failUnless(round(lon, 2) == 4.03)
        self.failUnless(round(alt) == 707.0) 
