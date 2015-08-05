# -*- coding: utf-8 -*-

import json
from forge.lib.global_geodetic import GlobalGeodetic


class TerrainMetadata:

    def __init__(self, *args, **kwargs):

        self.bounds = kwargs.get('bounds')
        self.tileMinZoom = kwargs.get('minzoom')
        self.tileMaxZoom = kwargs.get('maxzoom')

        self.available = [[] for i in range(self.tileMinZoom, self.tileMaxZoom + 1)]
        self.meta = dict(
            tilejson=kwargs.get('tilejson', '2.1.0'),
            name=kwargs.get('name', None),
            description=kwargs.get('version', '2.0.0'),
            format=kwargs.get('format', 'quantized-mesh-1.0'),
            attribution=kwargs.get('attribution', None),
            scheme=kwargs.get('scheme', 'tms'),
            tiles=[kwargs.get('tiles', '{z}/{x}/{y}.terrain?v={version}')],
            minzoom=self.tileMinZoom,
            maxzoom=self.tileMaxZoom,
            bounds=kwargs.get('bounds', [-180, -90, 180, 90]),
            projection=kwargs.get('projection', 'EPSG:4326'),
            available=kwargs.get('available', self.available)
        )

        self._initPyramidMetadata()

    # [[A, B],...,[G, H]] range of x values
    def removeTile(self, x, y, z):
        tileMinX = self.metadata[z]['x'][0]
        tileMaxX = self.metadata[z]['x'][1]

        if y not in self.ranges[z]:
            self.ranges[z][y] = self._createRanges(tileMinX, tileMaxX, x)
        else:
            newRanges = []
            for r in self.ranges[z][y]:
                newRanges += self._createRanges(r[0], r[1], x)
            self.ranges[z][y] = newRanges

    # Multi geometries are not supported
    def toJSON(self):

        for z in range(self.tileMinZoom, self.tileMaxZoom + 1):
            tileMinX = self.metadata[z]['x'][0]
            tileMaxX = self.metadata[z]['x'][1]
            tileMinY = self.metadata[z]['y'][0]
            tileMaxY = self.metadata[z]['y'][1]

            for y in xrange(tileMinY, tileMaxY + 1):
                # Holding data for layers.json
                # The whole range over x is available -> only one range
                if y not in self.ranges[z]:
                    if y == tileMinY:
                        # We only care about x values
                        previousRow = [[tileMinX, tileMaxX]]
                        previousRec = [
                            self._createRectangle(tileMinX, tileMaxX, tileMinY, tileMinY)
                        ]

                    newRow = [[tileMinX, tileMaxX]]
                    # Current row over x is equal to previous row -> increase rectangle size over y
                    if previousRow[0][0] == newRow[0][0] and \
                            previousRow[0][1] == newRow[0][1]:
                        previousRec[0]['endY'] = y
                    # Move temp rectangle in the final list, create new temp rec
                    else:
                        self.available[z - self.tileMinZoom] += previousRec
                        previousRec = [
                            self._createRectangle(tileMinX, tileMaxX, y, y)
                        ]

                # Use custom ranges
                else:
                    isEqual = True
                    newRow = self.ranges[z][y]
                    if y == tileMinY:
                        isEqual = False
                    else:
                        for i in xrange(0, len(newRow)):
                            # Simplification for now, only identical ranges can be merged
                            if len(previousRow) >= i + 1:
                                pRange = previousRow[i]
                                nRange = newRow[i]
                                # Different ranges
                                if pRange[0] != nRange[0] or pRange[1] != nRange[1]:
                                    isEqual = False
                                    break
                            else:
                                isEqual = False
                    # Previous row doesn't change and previous rectangle changes over y
                    if isEqual:
                        for i in range(0, len(previousRec)):
                            previousRec[i]['endY'] = y
                    else:
                        if y == tileMinY:
                            previousRec = []
                            for r in newRow:
                                previousRec.append(self._createRectangle(r[0], r[1], y, y))
                        else:
                            self.available[z - self.tileMinZoom] += previousRec
                            previousRec = []
                            for r in newRow:
                                previousRec.append(self._createRectangle(r[0], r[1], y, y))
                previousRow = newRow

            # Finally push the last rec
            self.meta['available'][z - self.tileMinZoom] += previousRec

        return json.dumps(self.meta)

    def _createRectangle(self, startX, endX, startY, endY):
        return {
            'startX': startX,
            'endX': endX,
            'startY': startY,
            'endY': endY
        }

    def _createRanges(self, minVal, maxVal, breakVal):
        if breakVal == minVal and breakVal == maxVal:
            return []
        elif breakVal == minVal:
            return [[breakVal + 1, maxVal]]
        elif breakVal == maxVal:
            return [[minVal, breakVal - 1]]
        elif breakVal > minVal and breakVal < maxVal:
            return [[minVal, breakVal - 1], [breakVal + 1, maxVal]]
        elif breakVal < minVal:
            return [[minVal, maxVal]]
        elif breakVal > maxVal:
            return [[minVal, maxVal]]

    def _initPyramidMetadata(self):
        # It keeps track of the starting and ending tiles
        # and the missing tiles in between
        self.metadata = {}
        self.ranges = {}
        geodetic = GlobalGeodetic(True)
        bounds = self.meta['bounds']
        # Assume the whole extent is available
        for z in range(self.tileMinZoom, self.tileMaxZoom + 1):
            tileMinX, tileMinY = geodetic.LonLatToTile(bounds[0], bounds[1], z)
            tileMaxX, tileMaxY = geodetic.LonLatToTile(bounds[2], bounds[3], z)
            self.metadata[z] = dict(
                x=[tileMinX, tileMaxX],
                y=[tileMinY, tileMaxY]
            )
            self.ranges[z] = {}
