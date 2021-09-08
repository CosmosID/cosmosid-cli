"""Representation of Reports."""
import json
import logging
import os
import time
import urllib.request
from os.path import expanduser, isdir, isfile, join, normpath, split, splitext
from urllib.parse import urlparse

import requests
from cosmosid.api.files import Runs
from cosmosid.helpers.exceptions import (AuthenticationFailed,
                                         FileExistsException, NotFound,
                                         NotFoundException, StatusException,
                                         ValidationError, ReportGenerationFailed,
                                         ReportGenerationTimeout)
from cosmosid.utils import progress, requests_retry_session

LOGEGR = logging.getLogger(__name__)

class RunReportResponseStatus:
    CREATED = "created"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class Reports(object):
    _resource_path = '/api/metagenid/v2/files/report/tsv'

    def __init__(self, base_url=None, api_key=None, file_id=None):
        self.base_url = base_url
        self.logger = LOGEGR
        self.header = {'X-Api-Key': api_key}
        self.report_type = None
        self.file_id = file_id
        self.run_o = Runs(base_url=self.base_url,
                          api_key=self.header['X-Api-Key'])
        self.session = requests_retry_session(self.header)
        self.session.headers.update()

    def await_report_task(self, task_id, timeout=5*60):
        task_url = f"{self.base_url}/api/metagenid/v2/files/report/{task_id}"
        start_time = time.time()
        self.logger.info("Awaiting the report task to be scheduled and complete.")
        while time.time() < start_time + timeout:
            result = self.session.get(task_url, headers=self.header)
            result.raise_for_status()
            task_data = json.loads(result.text)
            if task_data['status'] == RunReportResponseStatus.COMPLETED:
                progress(1, 1, f"Status: {task_data['status']}")
                return task_data['payload']
            if task_data['status'] == RunReportResponseStatus.FAILED:
                error = str(task_data['error'])
                progress(1, 1, f"Status: {task_data['status']}")
                raise ReportGenerationFailed(
                    f"Can't complete the report task {task_id}. "
                    f"Error: {error}")
            progress((time.time() - start_time), timeout, f"Status: {task_data['status']}")
            time.sleep(1)
        progress(1, 1, f"Status: Timeout")
        raise ReportGenerationTimeout()


    def get_report_url(self):
        """Return URL for download."""
        params = dict()
        try:
            request_url = "{}{}".format(self.base_url,
                                        self.__class__._resource_path)
            if not self.file_id:
                raise ValidationError('File ID is required')

            # TODO: propagate supported type and tax_level
            params = {"files": [self.file_id]}
            results = self.session.post(
                request_url, json=params, headers=self.header)

            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key')
            # TODO: check wheter it applicable on v2
            if results.status_code == 400:
                raise StatusException('File has a NON SUCCESS status')

            if results.status_code == 404:
                raise NotFound('File with given ID does '
                               'not exist: {}'.format(self.file_id))
            results.raise_for_status()
            task_resp = results.json()
            result = self.await_report_task(task_id=task_resp['id'])
            result.update(status=1)
            return result

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
