-- this function requires postgis >= 2.0.0 with raster support
CREATE OR REPLACE FUNCTION public.bgdi_watermask_rasterize(bbox geometry, width integer, height integer, watermask_table regclass, watermask_geom_column text)
  RETURNS SETOF raster AS
$BODY$
DECLARE 
    sql     TEXT;
    xmin    float default xmin(bbox);
    ymin    float default ymin(bbox);
    xmax    float default xmax(bbox);
    ymax    float default ymax(bbox);
    scalex  float default (xmax-xmin)::float/width::float;
    scaley  float default -((ymax-ymin)::float/height::float);
    inside  integer;
    outside integer;
BEGIN
    IF EXISTS ( 
        select * from information_schema.columns
        where table_name=watermask_table::text
        and column_name=watermask_geom_column
    ) THEN 
    /*
    -- this query would be more performant but extent of raster result is not stable, does only cover geometry features...
    sql := '
    select 
    st_union(st_asraster(st_intersection('|| watermask_geom_column ||',st_envelope(raster)),raster,''1BB'',1,0,true)) as raster 
    FROM '|| watermask_table ||' vector, 
    ST_MakeEmptyRaster('|| width ||', '|| height ||', '|| xmin ||', '|| ymax ||', '|| scalex ||', '|| scaley ||', 0, 0, 4326) raster 
    WHERE st_intersects(vector.'|| watermask_geom_column ||',st_envelope(raster));';
    */

    -- this query returns a raster with a stable extent of 256x256 pixels
    -- raster type is 1BB
    -- pixel value 0: land 
    -- pixel value 1: lake
    -- if the tile geometry lies completely inside a lake a raster with one pixel with value 1 will be returned
    -- if the tile geometry lies completely outside the lakes a raster with one pixel with value 0 will be returned
    EXECUTE format('SELECT count(1) FROM %I where ST_ContainsProperly(%I,%L)',watermask_table,watermask_geom_column,bbox) INTO inside;
    EXECUTE format('SELECT count(1) FROM %I where st_intersects(%L,%I)',watermask_table,bbox,watermask_geom_column) INTO outside;
    IF outside = 0 THEN
        --RAISE NOTICE 'tile lies completely outside lakes';
        sql := 'SELECT st_addband(ST_MakeEmptyRaster(1,1,0,0,1,1 , 0, 0, 4326),''1BB''::text,0,0)';
        RETURN QUERY EXECUTE sql;
        RETURN;
    END IF;
    
    IF inside > 0 THEN
        --RAISE NOTICE 'tile lies completely inside a lake';
        sql := 'SELECT st_addband(ST_MakeEmptyRaster(1,1,0,0,1,1 , 0, 0, 4326),''1BB''::text,1,0)';
        RETURN QUERY EXECUTE sql;
        RETURN;
    END IF;

    sql := '
    WITH input as (
        SELECT st_addband(ST_MakeEmptyRaster('|| width ||', '|| height ||', '|| xmin ||', '|| ymax ||', '|| scalex ||', '|| scaley ||', 0, 0, 4326),''1BB''::text,1,0) raster 
    ),
    intersected as ( 
        select 
        st_union(st_asraster(st_intersection('|| watermask_geom_column ||',st_envelope(raster)),raster,''1BB'',1,0,true)) as raster 
        FROM '|| watermask_table ||' vector, input
        WHERE st_intersects(vector.'|| watermask_geom_column ||',st_envelope(input.raster))
    )
    select 
        ST_MapAlgebra(
        input.raster
        , 1
        , intersected.raster
        , 1
        , ''[rast2.val] + [rast1.val]''
        , ''1BB''
        , ''FIRST''
        , NULL
        , NULL
        , NULL)
    FROM 
        input, intersected 
    ';

    --RAISE NOTICE 'function parameters: xmin: % ymin: % xmax: % ymax: % scalex: % scaley: % watermask_table: % watermask_column % ', xmin,ymin,xmax,ymax,scalex,scaley,watermask_table,watermask_geom_column;
    --RAISE NOTICE 'sql: %',sql;
    RETURN QUERY EXECUTE sql;
    ELSE
        RAISE NOTICE 'could not open column % in table %',watermask_geom_column,watermask_table;
    END IF;
  
END
$BODY$
LANGUAGE plpgsql STABLE
COST 100;
