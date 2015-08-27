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
baseDir: /geodata/WGS84/
shapefiles: 128/,64/,32/,16/,8/
tablenames: bl_128m,bl_64m,bl_32m,bl_16m,bl_8m
modelnames: bl_128m,bl_64m,bl_32m,bl_16m,bl_8m

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
