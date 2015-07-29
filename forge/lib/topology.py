# -*- coding: utf-8 -*-

import math
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
        self.coordsLookup = {}
        self.indexData = []
        self.coords = []
        self.minLon = float('inf')
        self.minLat = float('inf')
        self.minHeight = float('inf')
        self.maxLon = float('-inf')
        self.maxLat = float('-inf')
        self.maxHeight = float('-inf')

    def __str__(self):
        msg = 'Min height:'
        msg += '\n%s' % self.minHeight
        msg += '\nMax height:'
        msg += '\n%s' % self.maxHeight
        msg += '\nuVertex length:'
        msg += '\n%s' % len(self.uVertex)
        msg += '\nuVertex list:'
        msg += '\n%s' % self.uVertex
        msg += '\nvVertex length:'
        msg += '\n%s' % len(self.vVertex)
        msg += '\nuVertex list:'
        msg += '\n%s' % self.vVertex
        msg += '\nhVertex length:'
        msg += '\n%s' % len(self.hVertex)
        msg += '\nhVertex list:'
        msg += '\n%s' % self.hVertex
        msg += '\nindexData length:'
        msg += '\n%s' % len(self.indexData)
        msg += '\nindexData list:'
        msg += '\n%s' % self.indexData
        msg += '\nNumber of triangles: %s' % (len(self.indexData) / 3)
        return msg

    def fromRingsCoordinates(self):
        self.index = 0
        # In order to optimize this a bit we might want to deal only with flat
        # coordinates as an input
        for ring in self.ringsCoordinates:
            self._buildTopologyFromRing(ring)
        del self.ringsCoordinates

    def fromFeatures(self):
        self.index = 0
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
        # Remove last point of the polygon and keep only 3 coordinates
        return points[0: len(points) - 1]

    # Inspired by http://stackoverflow.com/questions/1709283/how-can-i-sort-a-coordinate-list-for-a-rectangle-counterclockwise
    def _assureRingCounterClockWise(self, ring):
        if len(ring) != 3:
            raise TypeError('A ring must have exactly 3 coordinates.')

        mlat = sum(coord[0] for coord in ring) / float(len(ring))
        mlon = sum(coord[1] for coord in ring) / float(len(ring))

        def algo(coord):
            return (math.atan2(coord[0] - mlat, coord[1] - mlon) + 2 * math.pi) % (2 * math.pi)

        ring.sort(key=algo, reverse=True)
        return ring

    def _buildTopologyFromRing(self, ring):
        ring = self._assureRingCounterClockWise(ring)

        for coord in ring:
            lookupKey = ','.join([str(coord[0]), str(coord[1]), str(coord[2])])
            indexData = self._findVertexIndex(lookupKey)
            if indexData is not None:
                self.indexData.append(indexData)
            else:
                self.uVertex.append(coord[0])
                self.vVertex.append(coord[1])
                self.hVertex.append(coord[2])
                self.coordsLookup[lookupKey] = len(self.uVertex) - 1

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

                self.indexData.append(self.index)
                # Keep track of coordinates for bbsphere and friends
                self.coords.append(coord)
                self.index += 1
        self.coordsLookup = {}

    def _findVertexIndex(self, lookupKey):
        # Naive approach for now
        if lookupKey in self.coordsLookup:
            return self.coordsLookup[lookupKey]
        return None
