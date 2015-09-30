[Server]
host: ${dbtarget}
port: 5432

[Admin]
user: pgkogis
password: ${pgpass}

[Database]
name: forge_main
user: tileforge
password: tileforge

[Data]
baseDir: /geodata/smb/iwi/3DTerrain/2015/
shapefiles: DHM25/64/,NW/128/,NW/64/,NW/32/,NW/16/,NW/8/,NW/4/,NW/2/,NW/1/,NW/0.5/
tablenames: dhm25_64m,bl_128m,bl_64m,bl_32m,bl_16m,bl_8m,bl_4m,bl_2m,bl_1m,bl_0_5m
modelnames: dhm25_64m,bl_128m,bl_64m,bl_32m,bl_16m,bl_8m,bl_4m,bl_2m,bl_1m,bl_0_5m
lakes: /home/geodata/lakes/lakes.shp

# Paths must be absolute!
[Reprojection]
# Determine if you want to reproject the input file (1: yes, 0: no)
reproject: 1
# Determine if you want to keep the reprojected input file
keepfiles: 0
geosuiteCmd: /home/${username}/GeoSuiteCmdx64/GeoSuiteCmd.exe
# Temporary find a better location for that!
outDirectory: /geodata/tmp/
fromPFrames: lv95
toPFrames: wgs84-ed
fromAFrames: ln02
toAFrames: ellipsoid
logfile: /geodata/log/reprojections_geodata.log
errorfile: /geodata/log/reprojections_errors_geodata.log
