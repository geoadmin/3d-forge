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
baseDir: /geodata/share/
shapefiles: 256/,128/,64/,32/,128/,64/,32/,16/,8/,4/,2/,1/,0.5/
tablenames: dhm25_256m,dhm25_128m,dhm25_64m,dhm25_32m,bl_128m,bl_64m,bl_32m,bl_16m,bl_8m,bl_4m,bl_2m,bl_1m,bl_0_5m
modelnames: dhm25_256m,dhm25_128m,dhm25_64m,dhm25_32m,bl_128m,bl_64m,bl_32m,bl_16m,bl_8m,bl_4m,bl_2m,bl_1m,bl_0_5m
lakes: /home/geodata/lakes/lakes.shp

# Paths must be absolute!
[Reprojection]
# Determine if you want to reproject the input file (1: yes, 0: no)
reproject: 1
# Determine if you want to keep the reprojected input file
keepfiles: 0
# exe from geodesy (Jerome Ray)
geosuiteCmd: /home/${username}/GeoSuiteCmdx64/GeoSuiteCmd.exe
# Temporary find a better location for that!
outDirectory: /geodata/tmp/

# options for geosuite
# input projection
fromPFrames: lv95
# output projections (WGS84 non corrected to geoide)
toPFrames: wgs84-ed
# don't know but this is how it must be done
fromAFrames: ln02
toAFrames: ln02

logfile: /geodata/logs/reprojections_geodata.log
errorfile: /geodata/logs/reprojections_errors_geodata.log
