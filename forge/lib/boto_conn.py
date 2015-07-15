# -*- coding: utf-8 -*-

from boto import connect_s3
from boto.s3.key import Key


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


def writeToS3(b, path, content, origin, contentType='application/octet-stream'):
    headers = {'Content-Type': contentType}
    k = Key(b)
    k.key = path
    k.set_metadata('IWI_Origin', origin)
    headers['Content-Encoding'] = 'gzip'
    k.set_contents_from_file(content, headers=headers)
