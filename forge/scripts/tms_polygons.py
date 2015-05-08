# -*- coding: utf-8 -*-

import osgeo.ogr as ogr
import osgeo.osr as osr
from forge.lib.helpers import transformCoordinate
from forge.lib.global_geodetic import GlobalGeodetic


# The goal of this script it to generate a shapefile per pyramidi/zoom level containing
# a poylgon per tile following the TMS standards.
# Each polygon has Key attribute containing the z/x/y tile's coordinate

MINX = 420000.0
MAXX = 900000.0
MINY = 30000.0
MAXY = 350000.0

minWKT = 'POINT (%f %f)' % (MINX, MINY)
maxWKT = 'POINT (%f %f)' % (MAXX, MAXY)

minPoint = transformCoordinate(minWKT, 21781, 4326)
maxPoint = transformCoordinate(maxWKT, 21781, 4326)

MINX = minPoint.GetX()
MINY = minPoint.GetY()
MAXX = maxPoint.GetX()
MAXY = maxPoint.GetY()
print 'Extent :'
print [MINX, MINY, MAXX, MAXY]
MINZOOM = 3
MAXZOOM = 17

geodetic = GlobalGeodetic(True)
drv = ogr.GetDriverByName('ESRI Shapefile')

# Generate table with min max tile coordinates for all zoomlevels
for tz in range(MINZOOM, MAXZOOM + 1):
    tminx, tminy = geodetic.LonLatToTile(MINX, MINY, tz)
    tmaxx, tmaxy = geodetic.LonLatToTile(MAXX, MAXY, tz)

    dataSource = drv.CreateDataSource('%s.shp' % tz)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = dataSource.CreateLayer('%s' % tz, srs, ogr.wkbPolygon)
    fieldKey = ogr.FieldDefn('Key', ogr.OFTString)
    fieldKey.SetWidth(12)
    layer.CreateField(fieldKey)

    for tx in range(tminx, tmaxx + 1):
        for ty in range(tminy, tmaxy + 1):
            tileKey = '%s/%s/%s' % (tz, tx, ty)
            [xmin, ymin, xmax, ymax] = geodetic.TileBounds(tx, ty, tz)
            print 'Tile key'
            print tileKey
            print 'Tile bounds'
            print geodetic.TileBounds(tx, ty, tz)
            # Create polygon from bounds
            # https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#create-a-new-shapefile-and-add-data
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField('Key', tileKey)
            wkt = 'POLYGON ((%f %f, %f %f, %f %f, %f %f, %f %f))' % (xmin, ymin, xmax, ymin, xmax, ymax, xmin, ymax, xmin, ymin)
            polygon = ogr.CreateGeometryFromWkt(wkt)
            feature.SetGeometry(polygon)
            layer.CreateFeature(feature)
            feature.Destroy()
    dataSource.Destroy()
