# -*- coding: utf-8 -*-

import sys
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
        self.counter = 0
        if prefix is not None:
            self.prefix = prefix
        else:
            raise Exception('One must define a prefix')
        self.keysList = self.bucket.list(prefix=self.prefix)

    def delete(self):
        keysToDelete = []
        print 'Are you sure you want to delete all tiles starting with %s? (y/n)' % self.prefix
        answer = raw_input('> ')
        if answer.lower() != 'y':
            sys.exit(1)
        print 'Deleting keys for prefix %s...' % self.prefix
        for key in self.keysList:
            keysToDelete.append(key)
            if len(keysToDelete) % 1000 == 0:
                self._deleteKeysResults(self.bucket.delete_keys(keysToDelete))
                keysToDelete = []
        if len(keysToDelete) > 0:
            self._deleteKeysResults(self.bucket.delete_keys(keysToDelete))
        print '%s keys have been deleted' % self.counter

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

    def _deleteKeysResults(self, results):
        nbDeleted = len(results.deleted)
        print '%s could not be deleted.' % len(results.errors)
        print '%s have been deleted.' % nbDeleted
        self.counter += len(results.deleted)
