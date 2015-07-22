CREATE OR REPLACE FUNCTION _interpolate_height_on_plane(polygon geometry, point geometry)
  RETURNS geometry AS
$BODY$
DECLARE
    polygon geometry DEFAULT $1;
    point   geometry DEFAULT $2;
    plane_a geometry;
    plane_b geometry;
    plane_c geometry;
    plane_a_x float;
    plane_a_y float;
    plane_a_z float;
    plane_b_x float;
    plane_b_y float;
    plane_b_z float;
    plane_c_x float;
    plane_c_y float;
    plane_c_z float;
    output geometry DEFAULT NULL;
    point_x float;
    point_y float;
    point_z float;
    point_z_interpolated float;
    normal_x float;
    normal_y float;
    normal_z float;
    stuetz_a_x float;
    stuetz_a_y float;
    stuetz_a_z float;
    stuetz_b_x float;
    stuetz_b_y float;
    stuetz_b_z float;    
    d float;   
    tmp text;
BEGIN
RAISE NOTICE 'Funktionsparameter wurde uebergeben: % %',st_astext(polygon),st_astext(point);  
   -- check input polygon for number of vertices and dimension
   if sum(ST_NPoints(polygon))-1 != 3 or st_ndims(polygon) != 3 or st_ndims(point) != 3 then
                RAISE EXCEPTION 'number of vertices in input polygon: % - must be 3',sum(ST_NPoints(polygon))-1;
                RAISE EXCEPTION 'input polygon has: % dims - must have 3',st_ndims(polygon);
                RAISE EXCEPTION 'input point has: % dims - must have 3',st_ndims(point);
                RETURN NULL;
   end if; 
   plane_a := (ST_DumpPoints(polygon)).geom limit 1;
   plane_b := (ST_DumpPoints(polygon)).geom limit 1 offset 1;
   plane_c := (ST_DumpPoints(polygon)).geom limit 1 offset 2;
  
   plane_a_x := x(plane_a);
   plane_a_y := y(plane_a);
   plane_a_z := z(plane_a);
   plane_b_x := x(plane_b);
   plane_b_y := y(plane_b);
   plane_b_z := z(plane_b);
   plane_c_x := x(plane_c);
   plane_c_y := y(plane_c);
   plane_c_z := z(plane_c); 
   point_x   := x(point); 
   point_y   := y(point); 
   point_z   := z(point); 

    -- check if input point lies on a corner of polygon   
   if point_x::numeric(100,7)::text = plane_a_x::numeric(100,7)::text and point_y::numeric(100,7)::text = plane_a_y::numeric(100,7)::text then
                RAISE WARNING 'you hit a corner point % ',st_astext(point);
                RETURN plane_a;
   end if;
   if point_x::numeric(100,7)::text = plane_b_x::numeric(100,7)::text and point_y::numeric(100,7)::text = plane_b_y::numeric(100,7)::text then
                RAISE WARNING 'you hit a corner point % ',st_astext(point);
                RETURN plane_b;
   end if;
   if point_x::numeric(100,7)::text = plane_c_x::numeric(100,7)::text and point_y::numeric(100,7)::text = plane_c_y::numeric(100,7)::text then
                RAISE WARNING 'you hit a corner point % ',st_astext(point);
                RETURN plane_c;
   end if;  
      
   -- create stuetz a
   stuetz_a_x  := (plane_b_x - plane_a_x);
   stuetz_a_y  := (plane_b_y - plane_a_y);
   stuetz_a_z  := (plane_b_z - plane_a_z); 
   -- create stuetz b
   stuetz_b_x  := (plane_c_x - plane_a_x);
   stuetz_b_y  := (plane_c_y - plane_a_y);
   stuetz_b_z  := (plane_c_z - plane_a_z); 
   -- create normal vector
   normal_x  := (stuetz_a_y*stuetz_b_z)-(stuetz_a_z*stuetz_b_y);
   normal_y  := (stuetz_a_z*stuetz_b_x)-(stuetz_a_x*stuetz_b_z);
   normal_z  := (stuetz_a_x*stuetz_b_y)-(stuetz_a_y*stuetz_b_x);
   
   -- plane equation, interpolate z value
   d := (plane_a_x*normal_x)+(plane_a_y*normal_y)+(plane_a_z*normal_z);
   RAISE NOTICE 'TIN A % % %', plane_a_x,plane_a_y,plane_a_z;            
   RAISE NOTICE 'TIN B % % %', plane_b_x,plane_b_y,plane_b_z;           
   RAISE NOTICE 'TIN C % % %', plane_c_x,plane_c_y,plane_c_z;             
   RAISE NOTICE 'Normalvektor: ( nx: % ny: % nz: % ) d: %',normal_x,normal_y,normal_z,d;
   point_z_interpolated := (d - normal_x*point_x - normal_y*point_y) / normal_z;
   RAISE NOTICE 'interpolated height %', point_z_interpolated;                
   RAISE NOTICE 'Koordinatengleichung der Ebene: nx*px + ny*py +nz*pz = d -> (%*%) + (%*%) + (%*%) = %',normal_x,point_x,normal_y,point_y,normal_z,point_z_interpolated,d;
   output = st_setsrid(st_makepoint(point_x,point_y,point_z_interpolated),4326);
   RETURN output;           
   EXCEPTION 
                WHEN division_by_zero THEN
                RAISE WARNING 'DIVISION BY ZERO , returning input point';
                return point;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
 COST 100;
ALTER FUNCTION _interpolate_height_on_plane(polygon geometry, point geometry)
  OWNER TO forge_user;
GRANT EXECUTE ON FUNCTION _interpolate_height_on_plane(polygon geometry, point geometry) TO postgres;
GRANT EXECUTE ON FUNCTION _interpolate_height_on_plane(polygon geometry, point geometry) TO forge_user;
