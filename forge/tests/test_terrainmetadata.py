# -*- coding: utf-8 -*-

import unittest
from forge.terrain.metadata import TerrainMetadata

# 0 means that there is no tile
# 1 means that there is a tile
# To read from the bottom left
matrix_1 = [
    [1, 0, 1, 1],
    [1, 1, 0, 1]
]

matrix_2 = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 1, 1, 1],
    [1, 1, 1, 1, 0, 1, 1, 1]
]


class TestTerrainMetadata(unittest.TestCase):

    def testTerrainMetadataInit(self):
        minZoom = 1
        maxZoom = 1
        tMeta = TerrainMetadata(minzoom=minZoom, maxzoom=maxZoom)

        self.assertTrue(tMeta.metadata[minZoom]['x'][0] == 0)
        self.assertTrue(tMeta.metadata[minZoom]['x'][1] == 3)
        self.assertTrue(tMeta.metadata[minZoom]['y'][0] == 0)
        self.assertTrue(tMeta.metadata[minZoom]['y'][1] == 1)

        self.assertTrue(len(tMeta.available) == 1)

    def testTerrainMetadataAllTiles(self):
        minZoom = 1
        maxZoom = 2
        tMeta = TerrainMetadata(minzoom=minZoom, maxzoom=maxZoom)

        self.assertTrue(tMeta.metadata[minZoom]['x'][0] == 0)
        self.assertTrue(tMeta.metadata[minZoom]['x'][1] == 3)
        self.assertTrue(tMeta.metadata[minZoom]['y'][0] == 0)
        self.assertTrue(tMeta.metadata[minZoom]['y'][1] == 1)

        self.assertTrue(tMeta.metadata[maxZoom]['x'][0] == 0)
        self.assertTrue(tMeta.metadata[maxZoom]['x'][1] == 7)
        self.assertTrue(tMeta.metadata[maxZoom]['y'][0] == 0)
        self.assertTrue(tMeta.metadata[maxZoom]['y'][1] == 3)

        self.assertTrue(len(tMeta.available) == 2)

        # Assume all tiles are here
        # from metadata to meta
        tMeta.toJSON()
        self.assertTrue(len(tMeta.meta['available'][0]) == 0)
        self.assertTrue(len(tMeta.meta['available'][1]) == 1)
        self.assertTrue(len(tMeta.meta['available'][2]) == 1)

        self.assertTrue(tMeta.meta['available'][1][0]['startX'] == 0)
        self.assertTrue(tMeta.meta['available'][1][0]['endX'] == 3)
        self.assertTrue(tMeta.meta['available'][1][0]['startY'] == 0)
        self.assertTrue(tMeta.meta['available'][1][0]['endY'] == 1)

        self.assertTrue(tMeta.meta['available'][2][0]['startX'] == 0)
        self.assertTrue(tMeta.meta['available'][2][0]['endX'] == 7)
        self.assertTrue(tMeta.meta['available'][2][0]['startY'] == 0)
        self.assertTrue(tMeta.meta['available'][2][0]['endY'] == 3)

    def testTerrainMetadataSubset(self):
        minZoom = 1
        maxZoom = 2
        tMeta = TerrainMetadata(minzoom=minZoom, maxzoom=maxZoom)
        matrices = {minZoom: matrix_1, maxZoom: matrix_2}

        for z in range(minZoom, maxZoom + 1):
            minX = tMeta.metadata[z]['x'][0]
            maxX = tMeta.metadata[z]['x'][1]
            minY = tMeta.metadata[z]['y'][0]
            maxY = tMeta.metadata[z]['y'][1]

            # tile 0,0 == matrix maxX, 0
            for x in range(minX, maxX + 1):
                for y in range(minY, maxY + 1):
                    localX = x - minX
                    localY = (y - maxY) * -1
                    matrix = matrices[z]
                    # y and x inverted in local matrix
                    if matrix[localY][localX] == 0:
                        tMeta.removeTile(x, y, z)

        tMeta.toJSON()

        # Zoom 0 (empty ranges if not define)
        self.assertTrue(len(tMeta.meta['available'][0]) == 0)

        # Zoom 1
        self.assertTrue(tMeta.meta['available'][1][0]['startX'] == 0)
        self.assertTrue(tMeta.meta['available'][1][0]['endX'] == 1)
        self.assertTrue(tMeta.meta['available'][1][0]['startY'] == 0)
        self.assertTrue(tMeta.meta['available'][1][0]['endY'] == 0)

        self.assertTrue(tMeta.meta['available'][1][1]['startX'] == 3)
        self.assertTrue(tMeta.meta['available'][1][1]['endX'] == 3)
        self.assertTrue(tMeta.meta['available'][1][1]['startY'] == 0)
        self.assertTrue(tMeta.meta['available'][1][1]['endY'] == 0)

        self.assertTrue(tMeta.meta['available'][1][2]['startX'] == 0)
        self.assertTrue(tMeta.meta['available'][1][2]['endX'] == 0)
        self.assertTrue(tMeta.meta['available'][1][2]['startY'] == 1)
        self.assertTrue(tMeta.meta['available'][1][2]['endY'] == 1)

        self.assertTrue(tMeta.meta['available'][1][3]['startX'] == 2)
        self.assertTrue(tMeta.meta['available'][1][3]['endX'] == 3)
        self.assertTrue(tMeta.meta['available'][1][3]['startY'] == 1)
        self.assertTrue(tMeta.meta['available'][1][3]['endY'] == 1)

        # Zoom 2
        self.assertTrue(tMeta.meta['available'][2][0]['startX'] == 0)
        self.assertTrue(tMeta.meta['available'][2][0]['endX'] == 3)
        self.assertTrue(tMeta.meta['available'][2][0]['startY'] == 0)
        self.assertTrue(tMeta.meta['available'][2][0]['endY'] == 1)

        self.assertTrue(tMeta.meta['available'][2][1]['startX'] == 5)
        self.assertTrue(tMeta.meta['available'][2][1]['endX'] == 7)
        self.assertTrue(tMeta.meta['available'][2][1]['startY'] == 0)
        self.assertTrue(tMeta.meta['available'][2][1]['endY'] == 1)

        self.assertTrue(tMeta.meta['available'][2][2]['startX'] == 4)
        self.assertTrue(tMeta.meta['available'][2][2]['endX'] == 7)
        self.assertTrue(tMeta.meta['available'][2][2]['startY'] == 2)
        self.assertTrue(tMeta.meta['available'][2][2]['endY'] == 2)

        self.assertTrue(tMeta.meta['available'][2][3]['startX'] == 0)
        self.assertTrue(tMeta.meta['available'][2][3]['endX'] == 7)
        self.assertTrue(tMeta.meta['available'][2][3]['startY'] == 3)
        self.assertTrue(tMeta.meta['available'][2][3]['endY'] == 3)
