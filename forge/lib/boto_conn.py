# -*- coding: utf-8 -*-

import time
import logging
from boto import connect_s3
from boto.s3.key import Key

logging.getLogger('boto').setLevel(logging.CRITICAL)


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


class S3Keys:

    def __init__(self, prefix):
        self.bucket = getBucket()
        if prefix is not None:
            self.prefix = prefix
        else:
            raise Exception('One must define a prefix')
        self.keysList = self.bucket.list(prefix=self.prefix)

    def delete(self):
        count = 0
        keysToDelete = []
        print 'Deleting keys for prefix %s...' % self.prefix
        for key in self.keysList:
            keysToDelete.append(key)
            count += 1
            if len(keysToDelete) % 1000 == 0:
                temp = self.bucket.delete_keys(keysToDelete)
                print '%s could not be deleted.' % len(temp.errors)
                print '%s have been deleted.' % len(temp.deleted)
                keysToDelete = []
        if len(keysToDelete) > 0:
            self.bucket.delete_keys(keysToDelete)
        print '%s keys have been deleted' % count

    def listKeys(self):
        print 'Listing keys for prefix %s...' % self.prefix
        for key in self.keysList:
            print "{name}\t{size}\t{modified}".format(
                name=key.name,
                size=key.size,
                modified=key.last_modified,
            )
            # So that one can interrput it from keyboard
            time.sleep(.2)

    def count(self):
        print 'Counting keys for prefix %s...' % self.prefix
        nbKeys = len(list(self.keysList))
        print '%s keys have been found for prefix %s' % (nbKeys, self.prefix)
