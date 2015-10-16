CREATE OR REPLACE FUNCTION create_simplified_geom_table(tablename name, tolerance float)
RETURNS VOID AS $func$
BEGIN
  EXECUTE '
    DROP TABLE IF EXISTS '|| tablename ||';
    CREATE TABLE '|| tablename ||' AS (
      SELECT *
      FROM (SELECT 
        id, 
        ST_Transform(
          ST_SimplifyPreserveTopology(
            ST_Transform(the_geom, 21781),
            '|| tolerance ||'),
          4326) AS the_geom
      FROM lakes) AS simple_lakes
      WHERE simple_lakes.the_geom IS NOT NULL AND ST_IsValid(simple_lakes.the_geom)
    );
    CREATE INDEX '|| tablename||'_geom_idx
      ON '|| tablename ||'
      USING gist
      (the_geom);';
    
END
$func$
LANGUAGE plpgsql;
