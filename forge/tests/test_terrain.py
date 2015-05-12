# -*- coding: utf-8 -*-

import unittest
import os
from forge.models.terrain import TerrainTile


class TestTerrainTile(unittest.TestCase):

    def setUp(self):
        self.tmpfile = 'terrain.tmp'

    def tearDown(self):
        os.remove(self.tmpfile)

    def testReaderWriter(self):
        '''
        Circle jerk testing.
        We read the file with our reader
        We write this data with our writer to a temporary file
        We read this temporary file
        We compare the results
        '''
        ter = TerrainTile()
        # ter.fromFile('forge/data/quantized-mesh/0.terrain', 7.80938, 7.81773, 46.30261, 46.3079)
        # ter.fromFile('forge/data/quantized-mesh/raron.flat.1.terrain', 7.80938, 7.81773, 46.30261, 46.30790)
        ter.fromFile('forge/data/quantized-mesh/goms.mountains.1.terrain', 7.80938, 7.81773, 46.30261, 46.30799)
        ter.toFile(self.tmpfile)
        ter2 = TerrainTile()
        ter2.fromFile(self.tmpfile, 7.80938, 7.81773, 46.30261, 46.30799)

        # check headers
        self.failUnless(len(ter.header) > 0)
        self.assertEqual(len(ter.header), len(ter2.header))
        self.assertEqual(len(ter.header), len(TerrainTile.quantizedMeshHeader))
        for k, v in ter.header.iteritems():
            self.assertEqual(v, ter2.header[k], 'For k = ' + k)

        # check vertices
        self.failUnless(len(ter.u) > 0)
        self.failUnless(len(ter.v) > 0)
        self.failUnless(len(ter.h) > 0)
        self.assertEqual(len(ter.u), len(ter2.u))
        self.assertEqual(len(ter.v), len(ter2.v))
        self.assertEqual(len(ter.h), len(ter2.h))
        for i, v in enumerate(ter.u):
            self.assertEqual(v, ter2.u[i])
        for i, v in enumerate(ter.v):
            self.assertEqual(v, ter2.v[i])
        for i, v in enumerate(ter.h):
            self.assertEqual(v, ter2.h[i])

        # check indices
        self.failUnless(len(ter.indices) > 0)
        self.assertEqual(len(ter.indices), len(ter2.indices))
        for i, v in enumerate(ter.indices):
            self.assertEqual(v, ter2.indices[i], i)

        # check edges
        self.failUnless(len(ter.westI) > 0)
        self.assertEqual(len(ter.westI), len(ter2.westI))
        for i, v in enumerate(ter.westI):
            self.assertEqual(v, ter2.westI[i], i)

        self.failUnless(len(ter.southI) > 0)
        self.assertEqual(len(ter.southI), len(ter2.southI))
        for i, v in enumerate(ter.southI):
            self.assertEqual(v, ter2.southI[i], i)

        self.failUnless(len(ter.eastI) > 0)
        self.assertEqual(len(ter.eastI), len(ter2.eastI))
        for i, v in enumerate(ter.eastI):
            self.assertEqual(v, ter2.eastI[i], i)

        self.failUnless(len(ter.northI) > 0)
        self.assertEqual(len(ter.northI), len(ter2.northI))
        for i, v in enumerate(ter.northI):
            self.assertEqual(v, ter2.northI[i], i)
