# -*- coding: utf-8 -*-

from boto import connect_s3


def _getS3Conn(profileName='tms3d_filestorage'):
    try:
        conn = connect_s3(profile_name=profileName)
    except Exception as e:
        raise Exception('S3: Error during connection %s' % e)
    return conn


connS3 = _getS3Conn()


def getBucket(bucketName='tms3d.geo.admin.ch'):
    try:
        bucket = connS3.get_bucket(bucketName)
    except Exception as e:
        raise Exception('Error during connection %s' % e)
    return bucket
