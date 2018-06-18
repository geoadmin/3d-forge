[General]
# 3d bucket
bucketName: ${bucketname}
# user specific
profileName: ${profilename}
# terrain files base path
bucketpath: 1.0.0/ch.swisstopo.terrain.3d/default/20180601/4326/
# chunks per process (that's a maximum)
maxChunks: 50
# when using aws sqs queue, the name of the queue
sqsqueue: terrain_20150924
# proc factor (total processes = factor * num_cpus_on_machine)
procfactor: 1

[Extent]
# below is region around thun
#minLon: 7.49432
#maxLon: 7.69554
#minLat: 46.68688
#maxLat: 46.83431

# region du shape 1247-24 (adelboden)
#minLon: 7.639054568027739
#maxLon: 7.703188120002635
#minLat: 46.51718858644207
#maxLat: 46.548623546531424

# below is whole switzerland
minLon: 5.86725126512748
maxLon: 10.9209100671547
minLat: 45.8026860136571
maxLat: 47.8661652478939

[Extensions]
# watermask: 0 -> no watermask
# watermask: 1 -> include watermask (use table public.lakes per default)
watermask: 0
# lighting: 0 -> no light
# lighting: 1 -> include unit vectors
lighting: 0

[Zooms]
# Zoom level to tile
tileMinZ: 14
tileMaxZ: 17

[8]
# Should be replaced with dhm25_256
tablename: dhm25_256m

[9]
tablename: dhm25_128m

[10]
tablename: dhm25_64m

[11]
tablename: dhm25_64m

[12]
tablename: dhm25_32m

[13]
tablename: bl_32m

[14]
tablename: bl_2018_8m

[15]
tablename: bl_2018_2m

[16]
tablename: bl_2018_1m

[17]
tablename: bl_2018_0_5m

[18]
tablename: bl_0_5m
