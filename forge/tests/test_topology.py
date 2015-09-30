# -*- coding: utf-8 -*-

import unittest
from forge.terrain.topology import TerrainTopology

# Must be defined counter clock wise order
vertices_1 = [
    [2.1,  3.1,  3.3],
    [1.2,  1.5,  4.2],
    [3.2,  2.2,  4.5]
]

vertices_2 = [
    [1.2,  1.5,  4.2],
    [2.2,  1.1,  1.1],
    [2.1,  2.2,  3.3]
]


class TestTopology(unittest.TestCase):

    def testTopologyOneVertex(self):
        topology = TerrainTopology()
        topology.addVertices(vertices_1)
        topology.create()

        self.assertTrue(len(topology.vertices) == 3)
        self.assertTrue(len(topology.faces) == 1)

        self.assertTrue(topology.vertices[0][0] == vertices_1[0][0])
        self.assertTrue(topology.vertices[0][1] == vertices_1[0][1])
        self.assertTrue(topology.vertices[0][2] == vertices_1[0][2])

        self.assertTrue(topology.vertices[1][0] == vertices_1[1][0])
        self.assertTrue(topology.vertices[1][1] == vertices_1[1][1])
        self.assertTrue(topology.vertices[1][2] == vertices_1[1][2])

    def testTopologyTwoVertices(self):
        topology = TerrainTopology()
        topology.addVertices(vertices_1)
        topology.addVertices(vertices_2)
        topology.create()

        self.assertTrue(len(topology.vertices) == 5)
        self.assertTrue(len(topology.faces) == 2)

        # Make sure no extra vertice is inserted
        self.assertTrue(topology.vertices[1][0] == vertices_2[0][0])
        self.assertTrue(topology.vertices[1][1] == vertices_2[0][1])
        self.assertTrue(topology.vertices[1][2] == vertices_2[0][2])

        self.assertTrue(topology.faces[1][0] == 1)
        self.assertTrue(topology.faces[1][1] == 3)
        self.assertTrue(topology.faces[1][2] == 4)

        self.assertTrue(len(topology.indexData) == 6)
        self.assertTrue(len(topology.uVertex) == 5)
        self.assertTrue(len(topology.vVertex) == 5)
        self.assertTrue(len(topology.hVertex) == 5)

        self.assertTrue(topology.minLon == 1.2)
        self.assertTrue(topology.minLat == 1.1)
        self.assertTrue(topology.minHeight == 1.1)
        self.assertTrue(topology.maxLon == 3.2)
        self.assertTrue(topology.maxLat == 3.1)
        self.assertTrue(topology.maxHeight == 4.5)
