[Server]
host: ${dbhost}
port: 5432

[Admin]
user: pgkogis
password: ${pgpass}

[Database]
name: forge_main
user: tileforge
password: tileforge

[Data]
# Input shapefiles
baseDir: /var/local/efs-dev/geodata/bund/swisstopo/terrain_3D/DTM_2018/Shape/
shapefiles: 8/,2/,1/,0.5/
tablenames: bl_2018_8m,bl_2018_2m,bl_2018_1m,bl_2018_0_5m
modelnames: bl_2018_8m,bl_2018_2m,bl_2018_1m,bl_2018_0_5m
lakes: /home/geodata/lakes/lakes.shp

# Paths must be absolute!
[Reprojection]
# Determine if you want to reproject the input file (1: yes, 0: no)
reproject: 1
# Determine if you want to keep the reprojected input file
keepfiles: 0
# exe from geodesy (Jerome Ray)
geosuiteCmd: /root/Console/x64/GeoSuiteCmd.exe
# Temporary find a better location for that!
outDirectory: /mnt/output-3d-forge/
# options for geosuite
# input projection
fromPFrames: lv95
# output projections (WGS84 non corrected to geoide)
toPFrames: wgs84-ed
# don't know but this is how it must be done
fromAFrames: ln02
toAFrames: ln02

logfile: /var/log/3d-forge/reprojections_geodata.log
errorfile: /var/log/3d-forge/reprojections_errors_geodata.log
