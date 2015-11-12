# -*- coding: utf-8 -*-

from forge.lib.tilejson import _TileJSON


class LayerMetadata(_TileJSON):

    def __init__(self, *args, **kwargs):

        defaultExtent = [
            5.86725126512748, 45.8026860136571,
            10.9209100671547, 47.8661652478939
        ]
        self.useGlobalTiles = False
        self.tileMinZoom = kwargs.get('minzoom')
        self.tileMaxZoom = kwargs.get('maxzoom')
        self.baseUrls = kwargs.get('baseUrls')
        if not self.baseUrls:
            raise ValueError('No base URL(s) provided, please complete the config file.')

        self.available = [[] for i in range(self.tileMinZoom, self.tileMaxZoom + 1)]

        self.meta = dict(
            tilejson     = kwargs.get('tilejson', '2.1.0'),
            name         = kwargs.get('name', None),
            description  = kwargs.get('version', ''),
            format       = kwargs.get('format', ''),
            attribution  = kwargs.get('attribution', None),
            scheme       = kwargs.get('scheme', 'tms'),
            tiles        = kwargs.get('tiles', self.baseUrls),
            minzoom      = self.tileMinZoom,
            maxzoom      = self.tileMaxZoom,
            bounds       = kwargs.get('bounds', defaultExtent),
            projection   = kwargs.get('projection', 'EPSG:4326'),
            available    = kwargs.get('available', self.available)
        )

        self._initPyramidMetadata()
