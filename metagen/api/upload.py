
import os
import sys
import threading
import boto3
import requests
import json
import logging
from boto3.s3.transfer import TransferConfig, ProgressCallbackInvoker
from s3transfer.utils import OSUtils
from botocore.exceptions import ClientError
from boto3.exceptions import RetriesExceededError, S3UploadFailedError
from metagen import utils

from metagen.helpers.upload import CosmosIdTransferManager
from metagen.helpers.exceptions import UploadException, AuthenticationFailed

logger = logging.getLogger(__name__)


class CosmosIdS3Client(object):

    _bfresource = '/api/metagenid/v1/files/upload_bfile'
    _sfresource = '/api/metagenid/v1/files/upload_sfile'

    def __init__(self, **kwargs):

        self.base_url = kwargs['base_url']
        self.api_key = kwargs['api_key']
        self.header = {'X-Api-Key': self.api_key}
        self.burl = self.base_url + self._bfresource
        self.surl = self.base_url + self._sfresource

    def create_multipart_upload(self, *args, **kwargs):

        data = dict(kwargs)
        mp_up = requests.put(self.burl, json=data, headers=self.header)
        resp = dict()
        if mp_up.status_code == requests.codes.ok:
            resp = mp_up.json()
        return resp

    def abort_multipart_upload(self, *args, **kwargs):

        data = dict(kwargs)
        ab_mp = requests.delete(self.burl, json=data, headers=self.header)
        return ab_mp.json()

    def upload_part(self, *args, **kwargs):
        data = dict(kwargs)
        resp = None
        upload_body = data.pop('Body')
        url_ = requests.get(self.burl, json=data, headers=self.header)
        if url_.status_code == requests.codes.ok:
            resp = requests.put(url_.json(), upload_body)
        return dict(resp.headers)

    def put_object(self, *args, **kwargs):
        data = dict(kwargs)
        upload_body = data.pop('Body')
        resp = None
        url_ = requests.get(self.surl, json=data, headers=self.header)
        if url_.status_code == requests.codes.ok:
            resp = requests.put(url_.json(), upload_body)
        return dict(resp.headers)

    def complete_multipart_upload(self, *args, **kwargs):
        data = dict(kwargs)
        cmp_up = requests.post(self.burl, json=data, headers=self.header)
        return cmp_up.json()


def upload_file(**kwargs):
    """Upload manager."""
    filename = kwargs.pop('file')
    client = CosmosIdS3Client(**kwargs)
    config = TransferConfig()
    osutil = OSUtils()
    transfer_manager = CosmosIdTransferManager(client, config=config, osutil=osutil)

    subscribers = None

    _, file_name = os.path.split(filename)
    try:
        response = requests.get(client.base_url + '/api/metagenid/v1/files/upload_init',
                                json=dict(file_name=file_name),
                                headers=client.header
                                )
        if response.status_code == 403:
            raise AuthenticationFailed('Authentication Failed. Wrong API Key.')
        if response.status_code == requests.codes.ok:
            sources = response.json()
            future = transfer_manager.upload(
                filename, sources['upload_source'], sources['upload_key'], None, subscribers)
            s3path, _ = os.path.split(sources['upload_key'])
            data = dict(path=s3path, size=str(os.stat(filename)[6]), name=file_name, parent='')
        else:
            logger.error("File upload inititalisation Failed. Response code: {}".format(response.status_code))
            raise UploadException("File upload inititalisation Failed. Response code: {}".format(response.status_code))

        future.result()
        create_response = requests.post(client.base_url + '/api/metagenid/v1/files',
                                        json=data,
                                        headers=client.header
                                        )
        if create_response.status_code == 201:
            return create_response.json()
        else:
            raise UploadException('Failed to upload file: {}'.format(file_name))
        '''
           If a client error was raised, add the backwards compatibility layer
           that raises a S3UploadFailedError. These specific errors were only
           ever thrown for upload_parts but now can be thrown for any related
           client error.
        '''
    except ClientError as e:
        raise S3UploadFailedError(
            "Failed to upload %s to %s: %s" % (
                filename, '/'.join([sources['upload_source'], sources['upload_key']]), e))
        return False
    except AuthenticationFailed as ae:
        logger.error('{}'.format(ae))
        return False
    except UploadException as ue:
        logger.error("File Upload Failed. Error: {}".format(ue))
        return False
