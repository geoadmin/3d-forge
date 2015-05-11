# -*- coding: utf-8 -*-

import unittest
from forge.lib.llh_ecef import LLH2ECEF, ECEF2LLH

# Conversion reference
# http://www.oc.nps.edu/oc2902w/coord/llhxyz.htm


class TestLLFECEF(unittest.TestCase):

    def testLLFToECEF(self):
        (lat, lon, alt) = (0, 0, 0)
        (x, y, z) = LLH2ECEF(lat, lon, alt)
        self.assertEqual(x, 6378137.0)
        self.assertEqual(y, 0.0)
        self.assertEqual(z, 0.0)

        # Swiss like lat/lon/alt (Bern)
        (lat, lon, alt) = (46.951103, 7.43861, 552)
        (x, y, z) = LLH2ECEF(lat, lon, alt)
        self.assertEqual(round(x, 2), 4325328.22)
        self.assertEqual(round(y, 2), 564726.19)
        self.assertEqual(round(z, 2), 4638459.21)

        # Swiss like lat/lon/alt (Raron)
        (lat, lon, alt) = (46.30447, 7.81512, 635.0)
        (x, y, z) = LLH2ECEF(lat, lon, alt)
        self.assertEqual(round(x, 2), 4373351.17)
        self.assertEqual(round(y, 2), 600250.39)
        self.assertEqual(round(z, 2), 4589151.29)

        # Swiss like lat/lon/alt (near Raron)
        (lat, lon, alt) = (46.306686, 7.81471, 635.0)
        (x, y, z) = LLH2ECEF(lat, lon, alt)
        self.assertEqual(round(x, 2), 4373179.0)
        self.assertEqual(round(y, 2), 600194.88)
        self.assertEqual(round(z, 2), 4589321.47)

    def testECEF2LLH(self):
        (x, y, z) = (0, 0, 6358000)
        # (lat, lon, alt) = ECEF2LLH(x, y, z)
        # self.assertEqual(lat, 90.0)
        # self.assertEqual(lon, 0.0)
        # self.assertEqual(round(z), 6358000.0)

        # Swiss like x/y/z (Bern)
        (x, y, z) = (4325328.22, 564726.19, 4638459.21)
        (lat, lon, alt) = ECEF2LLH(x, y, z)
        self.assertEqual(round(lat, 6), 46.951103)
        self.assertEqual(round(lon, 5), 7.43861)
        self.assertEqual(round(alt), 552)

        # Swiss like x/y/z (near Raron)
        (x, y, z) = (4373351.17, 600250.39, 4589151.29)
        (lat, lon, alt) = ECEF2LLH(x, y, z)
        self.assertEqual(round(lat, 6), 46.30447)
        self.assertEqual(round(lon, 5), 7.81512)
        self.assertEqual(round(alt), 635.0)

        # (x, y, z) = (4372744.359824215, 600135.4201770603, 4588862.366163889)
        (x, y, z) = (4373179.0, 600194.88, 4589321.47)
        (lat, lon, alt) = ECEF2LLH(x, y, z)
        self.assertEqual(round(lat, 6), 46.306686)
        self.assertEqual(round(lon, 5), 7.81471)
        self.assertEqual(round(alt), 635.0)
