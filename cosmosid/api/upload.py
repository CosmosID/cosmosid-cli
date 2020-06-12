"""Interactions with CosmosID's and S3's APIs regarding file uploads to S3."""

import logging
import os
import sys
import types

import boto3
import requests
from boto3.exceptions import S3UploadFailedError
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from s3transfer.manager import TransferManager
from s3transfer.subscribers import BaseSubscriber
from s3transfer.utils import OSUtils, ReadFileChunk

from cosmosid.api.files import Files
from cosmosid.api import urls
from cosmosid.helpers.exceptions import (AuthenticationFailed,
                                         NotEnoughCredits, NotFoundException,
                                         UploadException)
from cosmosid.utils import (do_not_retry_event, requests_retry_session, retry, LOCK)

LOGGER = logging.getLogger(__name__)
KB = 1024
MB = 1024 * KB
GB = 1024 * MB
MULTIPART_THRESHOLD = 1 * GB
MAX_CHUNK_SIZE = 5 * GB
if sys.platform.startswith('win'):
    MAX_CHUNK_SIZE = 1.9 * GB
MIN_CHUNK_SIZE = 1 * GB
MAX_CONCURRENCY = 5


class OSUtilsWithCallbacks(OSUtils):
    """Abstruction for manipulations on file[-like] objects."""

    def open_file_chunk_reader(self, filename, start_byte, size, callbacks):
        return ReadFileChunk.from_filename(filename, start_byte,
                                           size, callbacks,
                                           enable_callbacks=True)

    def open_file_chunk_reader_from_fileobj(self, fileobj, chunk_size,
                                            full_file_size, callbacks,
                                            close_callbacks=None):
        return ReadFileChunk(fileobj, chunk_size, full_file_size,
                             callbacks=callbacks, enable_callbacks=True,
                             close_callbacks=close_callbacks)


class ProgressSubscriber(BaseSubscriber):
    """Progress subscriber for any number of upload threads."""

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = LOCK

    def on_progress(self, future, bytes_transferred, **kwargs):
        """Callback to be invoked when progress is made on transfer."""
        with self._lock:
            self._seen_so_far += bytes_transferred
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %sMB / %sMB  (%.2f%%)" % (self._filename,
                                                 int(self._seen_so_far / MB),
                                                 int(self._size / MB),
                                                 percentage))
            sys.stdout.flush()


def create_client(base_url, api_key):
    """Create boto3 s3 client.

    Addss methods to the client for CosmosID's and S3's upload/download
    operations.
    """
    client = boto3.client('s3')
    client.base_url = base_url
    client.header = {'X-Api-Key': api_key}
    client.burl = client.base_url + urls.UPLOAD_BFILE_URL
    client.surl = client.base_url + urls.UPLOAD_SFILE_URL
    client.create_multipart_upload = types.MethodType(create_multipart_upload,client)
    client.abort_multipart_upload = types.MethodType(abort_multipart_upload,client)
    client.upload_part = types.MethodType(upload_part, client)
    client.put_object = types.MethodType(put_object, client)
    client.complete_multipart_upload = types.MethodType(complete_multipart_upload, client)
    return client


@retry(logger=LOGGER, tries=2)
def create_multipart_upload(self, *args, **kwargs):
    """Requests to CosmosID's API to initiate the multipart upload."""
    data = dict(kwargs)
    mp_up = requests.put(self.burl, json=data, headers=self.header, timeout=10)
    resp = dict()
    if mp_up.status_code == requests.codes.ok:
        resp = mp_up.json()
    return resp


@retry(logger=LOGGER, tries=3)
def abort_multipart_upload(self, *args, **kwargs):
    """Requests to CosmosID's API to do the cleanup.

    Amazon S3 retains all the parts until you either complete or abort the
    upload. Throughout its lifetime, you are billed for all storage,
    bandwidth, and requests for this multipart upload and its associated parts.
    """
    data = dict(kwargs)
    ab_mp = requests.delete(self.burl, json=data, headers=self.header,
                            timeout=5)
    if not ab_mp:
        raise Exception
    return ab_mp.json()


@retry(logger=LOGGER, tries=3)
def upload_part(self, *args, **kwargs):
    """Uploads data part to S3.

    Requests pre-signed URL from CosmosID's API. Uses it to upload data
    to S3.
    """
    data = dict(kwargs)
    resp = None
    upload_body = data.pop('Body')
    url_ = requests.get(self.burl, json=data, headers=self.header, timeout=5)
    if url_.status_code == requests.codes.ok:
        resp = requests.put(url_.json(), upload_body)
        if resp.headers:
            return dict(resp.headers)
    raise Exception('Upload issues.')


@retry(logger=LOGGER, tries=3)
def put_object(self, *args, **kwargs):
    """Upload small file.

    Requests pre-signed URL from CosmosID's API. Uses it to upload file
    to S3."""
    data = dict(kwargs)
    upload_body = data.pop('Body')
    resp = None
    url_ = requests.get(self.surl, json=data, headers=self.header)
    if url_.status_code == requests.codes.ok:
        resp = requests.put(url_.json(), upload_body)
        if resp.headers:
            return dict(resp.headers)
    raise Exception('Upload issues.')


@retry(logger=LOGGER, tries=3)
def complete_multipart_upload(self, *args, **kwargs):
    """Complete multipart upload.

    Makes requests to CosmosID's API in order to complete a multipart
    upload by assembling previously uploaded parts. It's been mentioned
    somwhere in the docs that consequent complete_multipart_uploads are OK
    for a short period after the upload is successfully completed.
    """
    data = dict(kwargs)
    cmp_up = requests.post(self.burl, json=data, headers=self.header,
                           timeout=60)
    if cmp_up:
        return cmp_up.json()
    raise Exception('complete_multipart_upload did not succeed.')


def upload_file(**kwargs):
    """Upload manager."""
    filename = kwargs.pop('file')
    parent_id = kwargs.pop('parent_id', None)
    multipart_chunksize = file_size = os.stat(filename)[6] #get size of file in bytes
    client = kwargs['client']

    if file_size > MULTIPART_THRESHOLD: #bigger that 1GB
        multipart_chunksize = min(int(file_size / 10), int(MAX_CHUNK_SIZE))
        multipart_chunksize = max(multipart_chunksize, int(MIN_CHUNK_SIZE))
        LOGGER.info('File size: %s MB', file_size / MB)
        LOGGER.info('Chunk size: %s MB', int(multipart_chunksize / MB))
    config = TransferConfig(multipart_threshold=MULTIPART_THRESHOLD,
                            max_concurrency=MAX_CONCURRENCY,
                            multipart_chunksize=multipart_chunksize)
    osutil = OSUtilsWithCallbacks()
    # Check if given parent folder exists
    if parent_id:
        fl_obj = Files(base_url=kwargs['base_url'], api_key=kwargs['api_key'])
        res = fl_obj.get_list(parent_id=parent_id)
        if not res['status']:
            raise NotFoundException('Parent folder for upload does '
                                    'not exists.')

    transfer_manager = TransferManager(client, config=config, osutil=osutil)

    subscribers = [ProgressSubscriber(filename), ]

    _, file_name = os.path.split(filename)
    try:
        init_url = client.base_url + urls.UPLOAD_INIT_URL
        response = requests_retry_session().put(init_url,
                                                json=dict(file_name=file_name),
                                                headers=client.header)
        if response.status_code == 402:
            raise NotEnoughCredits('Insufficient credits for upload.')
        if response.status_code == 403:
            raise AuthenticationFailed('Authentication Failed. Wrong API Key.')
        if response.status_code == requests.codes.ok:
            sources = response.json()
            future = transfer_manager.upload(
                filename,
                sources['upload_source'],
                sources['upload_key'],
                extra_args=None,
                subscribers=subscribers)
        else:
            LOGGER.error('File upload inititalisation Failed. '
                         'Response code: %s', response.status_code)
            raise UploadException('File upload inititalisation Failed. '
                                  'Response code: %s' % response.status_code)
        try:
            future.result()
        except KeyboardInterrupt:
            do_not_retry_event.set()
            return
        return sources['upload_key']

        # If a client error was raised, add the backwards compatibility layer
        # that raises a S3UploadFailedError. These specific errors were only
        # ever thrown for upload_parts but now can be thrown for any related
        # client error.

    except ClientError as error:
        raise S3UploadFailedError(
            "Failed to upload {} to {}: {}".format(
                filename,
                '/'.join([sources['upload_source'],
                          sources['upload_key']]),
                error))


def upload_and_save(files, parent_id, file_type, base_url, api_key):
    """
    Upload list of files and save them
    :param files: list of dicts where each file is:
        {
            'files': list of file paths,
            'sample_name': name of sample,
            'ext': files extension
        }
    :param parent_id: id of parent folder
    :param file_type: type of analysis (shotgun, amplicon, ...)
    :param base_url: base url of api
    :param api_key: api key of current user
    """
    client = create_client(base_url=base_url, api_key=api_key)
    try:
        items = []
        for file_name in files['files']:
            items.append(upload_file(client=client, file=file_name, file_type=file_type, parent_id=parent_id,
                                     api_key=api_key, base_url=base_url))
        data = dict(source=dict(type='web-upload', items=items),
                    sample_name=files['sample_name'],
                    folder_id=parent_id, file_type=file_type)
        create_file_url = client.base_url + urls.SAMPLES_URL
        create_response = requests_retry_session().post(
            create_file_url, json=data, headers=client.header)
        if create_response.status_code == 200:
            return create_response.json()
        else:
            raise UploadException('Failed to upload files: %s' % data['sample_name'])
    except NotEnoughCredits:
        LOGGER.error('Not Enough Credits')
        return False
    except AuthenticationFailed:
        LOGGER.error('Authentication Failed')
        return False
    except UploadException:
        LOGGER.error("File Upload Failed.")
        return False


def pricing(data, base_url, api_key):
    client = create_client(base_url=base_url, api_key=api_key)
    pricing_url = client.base_url + urls.SAMPLES_PRICING_URL
    pricing_response = requests_retry_session().post(url=pricing_url, json={'data': data}, headers=client.header)
    if pricing_response.status_code == 200:
        return pricing_response.json()
    else:
        pricing_response.raise_for_status()
