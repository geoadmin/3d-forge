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
        self.minLon = float('inf')
        self.minLat = float('inf')
        self.minHeight = float('inf')
        self.maxLon = float('-inf')
        self.maxLat = float('-inf')
        self.maxHeight = float('-inf')

    def __str__(self):
        str = 'Min height:'
        str += '\n%s' % self.minHeight
        str += '\nMax height:'
        str += '\n%s' % self.maxHeight
        str += '\nuVertex length:'
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
        str += '\nNumber of triangles: %s' % (len(self.indexData) / 3)
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
                    self.uVertex.append(coord[0])
                    self.vVertex.append(coord[1])
                    self.hVertex.append(coord[2])

                    if coord[0] < self.minLon:
                        self.minLon = coord[0]
                    if coord[1] < self.minLat:
                        self.minLat = coord[1]
                    if coord[2] < self.minHeight:
                        self.minHeight = coord[2]
                    if coord[0] > self.maxLon:
                        self.maxLon = coord[0]
                    if coord[1] > self.maxLat:
                        self.maxLat = coord[1]
                    if coord[2] > self.maxHeight:
                        self.maxHeight = coord[2]

                    self.indexData.append(index)
                    # Keep track of coordinates for bbsphere and friends
                    self.coords.append(coord)
                    index += 1

    def _findVertexIndex(self, coord):
        # Naive approach for now
        for i in xrange(0, len(self.uVertex)):
            if self.uVertex[i] == coord[0] and self.vVertex[i] == coord[1] and \
                    self.hVertex[i] == coord[2]:
                return i
        # Index doesn't exist yet
        return None
