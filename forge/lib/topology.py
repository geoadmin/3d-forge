# -*- coding: utf-8 -*-


from osgeo import ogr


class TerrainTopology(object):

    def __init__(self, features=None, ringsCoordinates=None):
        if features is None and ringsCoordinates is None:
            raise Exception('Please provide a list of GDAL features or rings coordinates')

        if features is not None:
            if not isinstance(features, list):
                raise TypeError('Please provide a list of GDAL features')
            if len(features) == 0:
                raise Exception('The list must contain at least one feature')

        if ringsCoordinates is not None:
            if not isinstance(ringsCoordinates, list):
                raise TypeError('Please provide a list of rings coordinates')
            if len(ringsCoordinates) == 0:
                raise Exception('The list must contain at least one ring')

        self.features = features
        self.ringsCoordinates = ringsCoordinates
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

    def fromRingsCoordinates(self):
        # In order to optimize this a bit we might want to deal only with flat
        # coordinates as an input
        for ring in self.ringsCoordinates:
            self._buildTopologyFromRing(ring)
        del self.ringsCoordinates

    def fromFeatures(self):
        for feature in self.features:
            if not isinstance(feature, ogr.Feature):
                raise TypeError('Only GDAL features are supported')
            geometry = feature.GetGeometryRef()
            dim = geometry.GetCoordinateDimension()
            if dim != 3:
                raise TypeError('A feature with a dimension of %s has been found.' % dim)

            ring = self._ringFromGDALGeometry(geometry)
            self._buildTopologyFromRing(ring)
        del self.features

    def _ringFromGDALGeometry(self, geometry):
        # 0 refers to the ring
        ring = geometry.GetGeometryRef(0)
        points = ring.GetPoints()
        if points[0] != points[len(points) - 1]:
            raise Exception('Last coord %s is not equal to the first coord %s' % (points[0], points[len(points) - 1]))
        # Remove last point of the polygon and keep only 3 coordinates
        return points[0: len(points) - 1]

    def _buildTopologyFromRing(self, ring):
        for coord in ring:
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

                self.indexData.append(len(self.uVertex) - 1)
                # Keep track of coordinates for bbsphere and friends
                self.coords.append(coord)

    def _findVertexIndex(self, coord):
        try:
            uI = self.uVertex.index(coord[0])
            vI = self.vVertex.index(coord[1])
            hI = self.hVertex.index(coord[2])
            if uI == vI == hI:
                return uI
        except ValueError:
            pass
        return None
