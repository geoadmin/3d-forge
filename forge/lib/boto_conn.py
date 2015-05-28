# -*- coding: utf-8 -*-

from boto import connect_s3


def _get_s3_conn(profileName='3dforge_filestorage'):
    try:
        conn = connect_s3(profile_name=profileName)
    except Exception as e:
        raise 'S3: Error during connection %s' % e
    return conn


conn_s3 = _get_s3_conn()


def get_bucket(bucketName='wroathiesiuxiefriepl-vectortiles'):
    try:
        bucket = conn_s3.get_bucket(bucketName)
    except Exception as e:
        raise 'Error during connection %s' % e
    return bucket
