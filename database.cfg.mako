[Server]
host: ${dbtarget}
port: 5432

[Admin]
user: pgkogis
password: ${pgpass}

[Database]
name: forge
user: tileforge
password: tileforge

[Data]
baseDir: /var/local/cartoweb/tmp/3dpoc/
shapefiles: MNT25Swizerland/,WGS84/64/,WGS84/32/,WGS84/16/,WGS84/8/,WGS84/4/,WGS84/2/,WGS84/1/,WGS84/0.5/,WGS84/0.25/
tablenames: mnt25_simplified_100m,break_lines_64m,break_lines_32m,break_lines_16m,break_lines_8m,break_lines_4m,break_lines_2m,break_lines_1m,break_lines_0_5m,break_lines_0_25m
modelnames: mnt25,bl_64m,bl_32m,bl_16m,bl_8m,bl_4m,bl_2m,bl_1m,bl_0_5m,bl_0_25m

# Paths must be absolute!
[Reprojection]
# Determine if you want to reproject the input file (1: yes, 0: no)
reproject: 0
# Determine if you want to keep the reprojected input file
keepfiles: 0
geosuiteCmd: mono /home/tileforge/GeoSuiteCmdx64/GeoSuiteCmd.exe
# Temporary find a better location for that!
outDirectory: /var/log/tileforge/
fromPFrames: lv95
toPFrames: wgs84-ed
fromAFrames: ln02
toAFrames: ellipsoid
logfile: /var/log/tileforge/reprojections.log
errorfile: /var/log/tileforge/reprojections_errors.log

[Logging]
config: logging.cfg
logfile: /var/log/tileforge/forge_%(timestamp)s.log
sqlLogfile: /var/log/tileforge/sql_%(timestamp)s.log
