# -*- coding: utf-8 -*-


from osgeo import ogr


class TerrainTopology(object):

    def __init__(self, features=None):
        if not isinstance(features, list):
            raise TypeError('Please provide a list of GDAL features')
        if len(features) == 0:
            raise Exception('The list must contain at least one feature')
        self.features = features
        self.uVertex = []
        self.vVertex = []
        self.hVertex = []
        self.indexData = []
        self.coords = []

    def __str__(self):
        str = 'uVertex length:'
        str += '\n%s' % len(self.uVertex)
        str += '\nuVertex list:'
        str += '\n%s' % self.uVertex
        str += '\nvVertex length:'
        str += '\n%s' % len(self.vVertex)
        str += '\nuVertex list:'
        str += '\n%s' % self.vVertex
        str += '\nhVertex length:'
        str += '\n%s' % len(self.hVertex)
        str += '\nhVertex list:'
        str += '\n%s' % self.hVertex
        str += '\nindexData length:'
        str += '\n%s' % len(self.indexData)
        str += '\nindexData list:'
        str += '\n%s' % self.indexData
        return str

    def create(self):
        index = 0
        for feature in self.features:
            if not isinstance(feature, ogr.Feature):
                raise TypeError('Only GDAL features are supported')
            geometry = feature.GetGeometryRef()
            assert geometry.GetCoordinateDimension() == 3, 'A feature with an unexpected dimension has been found.'
            # 0 refers to the ring
            ring = geometry.GetGeometryRef(0)
            points = ring.GetPoints()
            # Remove last point of the polygon and keep only 3 coordinates
            coords = points[0: len(points) - 1]
            for coord in coords:
                indexData = self._findVertexIndex(coord)
                if indexData is not None:
                    self.indexData.append(indexData)
                else:
                    self.uVertex.append(coords[0])
                    self.vVertex.append(coords[1])
                    self.hVertex.append(coords[2])
                    self.indexData.append(index)
                    # Keep track of coordinates for bbsphere and friends
                    self.coords.append(coord)
                    index += 1

    def _findVertexIndex(self, coord):
        # Naive approach for now
        for i in range(0, len(self.uVertex)):
            if self.uVertex[i] == coord[0]:
                if self.vVertex[i] == coord[1]:
                    return i
        # Index doesn't exist yet
        return None
