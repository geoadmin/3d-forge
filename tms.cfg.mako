[General]
# 3d bucket
bucketName: ${bucketname}
# user specific
profileName: ${profilename}
# terrain files base path
bucketpath: 1.0.0/ch.swisstopo.terrain.3d/default/20151231/4326/
# chunks per process (that's a maximum)
maxChunks: 50

[Extent]
minLon: 8.366
maxLon: 10.694
minLat: 45.798
maxLat: 46.898
# fullonly: 0 -> inludes all tiles that intersect, even partly, with extent
# fullonly: 1 -> include only tiles that fully intersect with extent
fullonly: 0

[Zooms]
tileMinZ: 9
tileMaxZ: 17

[9]
tablename: bl_128m

[10]
tablename: bl_64m

[11]
tablename: bl_64m

[12]
tablename: bl_32m

[13]
tablename: bl_16m

[14]
tablename: bl_8m

[15]
tablename: bl_4m

[16]
tablename: bl_4m

[17]
tablename: bl_4m

[18]
tablename: bl_4m
