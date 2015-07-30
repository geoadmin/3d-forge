
CREATE OR REPLACE FUNCTION bgdi_lonlat2tile(lon double precision DEFAULT 7.0, lat double precision DEFAULT 46.0, zoom integer DEFAULT 5)
  RETURNS geometry AS
$BODY$
  DECLARE
    -- formula from http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/globalmaptiles.py
    px double precision;
    py double precision;
    pz double precision;
    res double precision;
  BEGIN
    res = ((180.0 / 256.0 )/ (1 << zoom));
    px = (180.0 + lon) / res;
    py = (90 + lat) / res;
    px = floor( ceiling( px / 256.0 ) - 1 );
    py = floor( ceiling( py / 256.0 ) - 1 );
    pz = (1 << zoom) - py - 1;
    RETURN ST_SetSRID(ST_MakePoint(
      px,
      py,
      pz),
      4326);
  END
$BODY$
  LANGUAGE plpgsql IMMUTABLE STRICT
  COST 100;
    
CREATE OR REPLACE FUNCTION public.bgdi_global_geodetic_recursive(geom geometry,maxlevels integer)
RETURNS TABLE(id bigint,zoomlevel integer, x integer, y integer, the_geom geometry, label_tsm text, label_google text) AS
$BODY$
DECLARE
    tile_0_0        geometry;
    tile_1_0        geometry;
    maxlevels       integer = $2;
    looper      geometry;
    geoms       geometry[];
    geoms_nextlevel geometry[]; 
    counter     bigint = 0;
    xmin        double precision = 0;
    ymin        double precision = 0;
    xmax        double precision = 0;
    ymax        double precision = 0;
    tiles_y     bigint = 1;

BEGIN
    tile_0_0        := st_setsrid('BOX(-180 -90,0 90)'::box2d::geometry,4326);
    tile_1_0        := st_setsrid('BOX(0 -90,180 90)'::box2d::geometry,4326);
    geoms       := array[tile_0_0,tile_1_0]::geometry[];
    geoms_nextlevel := array[]::geometry[];
    

    /*
 http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/
 Global Geodetic System origin top left
 zoomlevel 0 contains two tiles
    
 zoomlevel 1
                 +90
          +-------+-------+
          |       |       |
 Google   |  0,1  |  1,1  |
 TSM      |  0,0  |  1,0  |
          |       |       |
   -180   +-------+-------+ +180
          |       |       |
 Google   |  0,0  |  1,0  |
 TSM      |  0,1  |  1,1  |
          |       |       |
          +-------+-------+
                 -90
    */

    FOR  i IN 0..maxlevels LOOP 
    tiles_y := (180.0 / (180.0 / ( 1 << i)))::integer;
    FOREACH looper in ARRAY geoms
    Loop
        --RAISE NOTICE 'geometry: %',st_astext(looper);
        IF st_intersects(looper,geom)  THEN
            --RAISE NOTICE 'lon2tile: % lat2tile: % x: % y: % zoom: % tiles_y: %',lon2tile(st_x(st_centroid(looper)),i),lat2tile(st_y(st_centroid(looper)),i),st_x(st_centroid(looper)),st_y(st_centroid(looper)),i,tiles_y;
            return query 
            select 
                counter as id
                , i as zoomlevel
                , lon2tile(st_x(st_centroid(looper)),i) as x
                , lat2tile(st_y(st_centroid(looper)),i) as y
                , st_setsrid(looper::geometry,4326) as the_geom
                , i||'/'||(st_x(bgdi_lonlat2tile(st_x(st_centroid(looper)),st_y(st_centroid(looper)),i)))||'/'||tiles_y-(st_y(bgdi_lonlat2tile(st_x(st_centroid(looper)),st_y(st_centroid(looper)),i)))-1 as label_tsm
                , i||'/'||(st_x(bgdi_lonlat2tile(st_x(st_centroid(looper)),st_y(st_centroid(looper)),i)))||'/'||(st_y(bgdi_lonlat2tile(st_x(st_centroid(looper)),st_y(st_centroid(looper)),i))) as label_google;
            counter := counter+1;
            geoms_nextlevel := array_append(geoms_nextlevel,looper);
        END IF;
    END LOOP;
    geoms := array[]::geometry[];
    FOREACH looper in ARRAY geoms_nextlevel
    LOOP
        -- divide into 4 equal polygons
        --RAISE NOTICE 'dividing looper %',st_astext(looper);
        xmin    := st_xmin(looper::box2d);
        xmax    := st_xmax(looper::box2d);
        ymin    := st_ymin(looper::box2d);
        ymax    := st_ymax(looper::box2d);
        geoms   := array_append(geoms,ST_Envelope(st_geomfromtext('LINESTRING('||xmin||' '||(ymin+((ymax-ymin)/2))||','||(xmin+((xmax-xmin)/2))||' '|| ymax||')',4326))); --top left
        geoms   := array_append(geoms,ST_Envelope(st_geomfromtext('LINESTRING('||xmin+((xmax-xmin)/2)||' '||ymin+((ymax-ymin)/2)||','||xmax||' '||ymax||')',4326))); --top right
        geoms   := array_append(geoms,ST_Envelope(st_geomfromtext('LINESTRING('||xmin||' '||ymin||','||xmin+((xmax-xmin)/2)||' '||ymin+((ymax-ymin)/2)||')',4326))); --bottom left
        geoms   := array_append(geoms,ST_Envelope(st_geomfromtext('LINESTRING('||xmin+((xmax-xmin)/2)||' '||ymin||','||xmax||' '||ymin+((ymax-ymin)/2)||')',4326))); --bottom right     
        
    END LOOP;
    geoms_nextlevel := array[]::geometry[];
    END LOOP;
    --return ( quadindex );
    return;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

/*
Execute function like that:
$ psql -c "select id,zoomlevel,x,y,st_astext(the_geom),label_tsm,label_google FROM bgdi_global_geodetic_recursive(st_setsrid('BOX(8.15974 46.75665,8.16465 46.75913)'::box2d::geometry, 4326),5);" -d forge
 id | zoomlevel | x  | y  |                            st_astext                            | label_tsm | label_google
----+-----------+----+----+-----------------------------------------------------------------+-----------+--------------
  0 |         0 |  1 |  0 | POLYGON((0 -90,0 90,180 90,180 -90,0 -90))                      | 0/1/0     | 0/1/0
  1 |         1 |  2 |  0 | POLYGON((0 0,0 90,90 90,90 0,0 0))                              | 1/2/0     | 1/2/1
  2 |         2 |  4 |  0 | POLYGON((0 45,0 90,45 90,45 45,0 45))                           | 2/4/0     | 2/4/3
  3 |         3 |  8 |  2 | POLYGON((0 45,0 67.5,22.5 67.5,22.5 45,0 45))                   | 3/8/1     | 3/8/6
  4 |         4 | 16 |  5 | POLYGON((0 45,0 56.25,11.25 56.25,11.25 45,0 45))               | 4/16/3    | 4/16/12
  5 |         5 | 32 | 11 | POLYGON((5.625 45,5.625 50.625,11.25 50.625,11.25 45,5.625 45)) | 5/33/7    | 5/33/24
(6 Zeilen)
*/
