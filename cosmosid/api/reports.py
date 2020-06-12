"""Representation of Reports."""
import logging
import os
import urllib.request
from os.path import expanduser, isdir, isfile, join, normpath, split, splitext
from urllib.parse import urlparse

import requests
from cosmosid.api.files import Runs
from cosmosid.helpers.exceptions import (AuthenticationFailed,
                                         FileExistsException, NotFound,
                                         NotFoundException, StatusException,
                                         ValidationError)

LOGEGR = logging.getLogger(__name__)


class Reports(object):
    _resource_path = '/api/metagenid/v1/files/{file_id}/csv'

    def __init__(self, base_url=None, api_key=None, file_id=None, run_id=None):
        self.base_url = base_url
        self.logger = LOGEGR
        self.header = {'X-Api-Key': api_key}
        self.report_type = None
        self.file_id = file_id
        self.run_id = run_id
        self.run_o = Runs(base_url=self.base_url,
                          api_key=self.header['X-Api-Key'])

    def __is_runid_in_file(self):
        """Get given run meta and check is the run in sample."""
        single_run = self.run_o.get_single_run(self.run_id)
        if single_run:
            if single_run['status']:
                if single_run['file']['id'] == self.file_id:
                    return True
        return False

    def get_report_url(self):
        """Return URL for download."""
        params = dict()
        try:
            request_url = "{}{}".format(self.base_url,
                                        self.__class__._resource_path)
            if not self.file_id:
                raise ValidationError('File ID is required')
            if self.run_id:
                if not self.__is_runid_in_file():
                    raise NotFound('Given Run id {} is not in '
                                   'given File {}'.format(self.run_id,
                                                          self.file_id))

            params.update(sample_run_id=self.run_id)
            request_url = request_url.format(file_id=self.file_id)
            results = requests.get(request_url, params=params,
                                   headers=self.header)
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key')
            if results.status_code == 406:
                raise StatusException('File has a NON SUCCESS status')
            if results.status_code == 404:
                raise NotFound('File with given ID does '
                               'not exist: {}'.format(self.file_id))
            if requests.codes.ok:
                resp = results.json()
                resp.update(status=1)
                return resp
            results.raise_for_status()
        except AuthenticationFailed:
            self.logger.error('Authentication Failed')
            return {'url': None}
        except StatusException:
            self.logger.error('StatusException')
            return {'url': 1}
        except NotFound:
            self.logger.error('Not Found')
            return {'url': None}
        except ValidationError:
            self.logger.error('Validation error')
            return
        except requests.exceptions.RequestException:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: %s', results.status_code)
            self.logger.debug('Debug', exc_info=True)

    def save_report(self, out_file=None, out_dir=None, block_size=8192):
        """Save file for given url to disk."""
        def _download_helper(response, out_f):
            if block_size is None:
                buffer = response.read()
                out_f.write(buffer)
            else:
                file_size_dl = 0
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    file_size_dl += len(buffer)
                    out_f.write(buffer)
        try:
            if out_dir:
                out_dir = expanduser(normpath(out_dir))
                if not isdir(out_dir):
                    raise NotFoundException('Destination directory does '
                                            'not exist: {}'.format(out_dir))
            else:
                out_dir = os.getcwd()
            report_data = self.get_report_url()

            if not report_data['url']:
                raise Exception('Empty report Url received')
            if report_data['url'] == 1:
                raise NotFoundException('Report can not be generated for file with NON SUCCESS status.')
            parsed_url = urlparse(report_data['url'])
            _, file_name = split(parsed_url.path)
            if out_file:
                out_file = expanduser(normpath(out_file))
                out_dir, file_name = split(out_file)

            _, extension = splitext(file_name)
            file_name = (file_name if extension == '.zip' else join(file_name + '.zip'))
            out_file = join(out_dir, file_name)
            if isfile(out_file):
                raise FileExistsException('Destination File exists: %s'
                                          % out_file)
            with open(out_file, "wb") as output:
                with urllib.request.urlopen(report_data['url']) as response:
                    _download_helper(response, output)

            return ({'status': 1, 'saved_report': out_file})
        except AuthenticationFailed as auth_error:
            self.logger.error('Authentication Failed')
            return {'status': 0, 'message': auth_error}
        except NotFoundException as nfe:
            self.logger.error('Not Found')
            return {'status': 0, 'message': nfe}
        except FileExistsException as file_exists_error:
            self.logger.error('File Exists')
            return {'status': 0, 'message': file_exists_error}
        except Exception as error:
            self.logger.error('Could not save report')
            return {'status': 0, 'message': error}
