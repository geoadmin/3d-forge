-- View: meta

CREATE OR REPLACE VIEW meta AS 
 SELECT a.relname AS "Table",
    pg_size_pretty(pg_total_relation_size(a.relid::regclass)) AS "Size Total",
    pg_size_pretty(pg_total_relation_size(a.relid::regclass) - pg_relation_size(a.relid::regclass)) AS "External Size",
    b.n_tup_ins - b.n_tup_del AS rowcount
   FROM pg_statio_user_tables a
     LEFT JOIN pg_stat_all_tables b ON a.relid = b.relid
  ORDER BY pg_total_relation_size(a.relid::regclass) DESC;

/*
prints the size of all the tables and their indices

ltclm@ip-10-220-6-191:~/3d-forge$ psql -d forge -c "SELECT * FROM meta;"
         Table         | Size Total | External Size | rowcount
-----------------------+------------+---------------+----------
 break_lines_0_25m     | 94 GB      | 27 GB         |        0
 break_lines_0_5m      | 38 GB      | 11 GB         |        0
 break_lines_1m        | 19 GB      | 5631 MB       |        0
 break_lines_2m        | 10078 MB   | 2968 MB       |        0
 break_lines_4m        | 1967 MB    | 575 MB        |        0
 break_lines_8m        | 904 MB     | 265 MB        |        0
 break_lines_16m       | 653 MB     | 194 MB        |        0
 break_lines_32m       | 458 MB     | 136 MB        |        0
 mnt25_simplified_100m | 390 MB     | 113 MB        |        0
 break_lines_64m       | 330 MB     | 96 MB         |        0
 spatial_ref_sys       | 3360 kB    | 176 kB        |        0
 topology              | 24 kB      | 24 kB         |        0
 layer                 | 24 kB      | 24 kB         |        0
 zoomlevel_6           | 16 kB      | 8192 bytes    |        1
 zoomlevel_4           | 16 kB      | 8192 bytes    |        1
 zoomlevel_3           | 16 kB      | 8192 bytes    |        1
 zoomlevel_8           | 16 kB      | 8192 bytes    |        1
 zoomlevel_2           | 16 kB      | 8192 bytes    |        1
 zoomlevel_7           | 16 kB      | 8192 bytes    |        1
 zoomlevel_5           | 16 kB      | 8192 bytes    |        1
 zoomlevel_0           | 16 kB      | 8192 bytes    |        1
 table_z17_extent      | 16 kB      | 8192 bytes    |        0
 zoomlevel_1           | 16 kB      | 8192 bytes    |        1

*/
