"""Representation of Reports."""
import logging
import requests
import urllib.request
import os
from urllib.parse import urlparse
from os.path import split, join, splitext, expanduser, normpath, isdir, isfile
from cosmosid.helpers.exceptions import (ValidationError, NotFoundException, StatusExeception,
                                         AuthenticationFailed, FileExistsException, NotFound)


logger = logging.getLogger(__name__)


class Reports(object):
    _resource_path = '/api/metagenid/v1/files/{file_id}/csv'

    def __init__(self, base_url=None, api_key=None, file_id=None):
        self.base_url = base_url
        self.logger = logger
        self.header = {'X-Api-Key': api_key}
        self.report_type = None
        self.file_id = file_id

    def get_report_url(self):
        """Return URL for download."""
        try:
            request_url = "{}{}".format(self.base_url, self.__class__._resource_path)
            if not self.file_id:
                raise ValidationError('File ID is required')
            request_url = request_url.format(file_id=self.file_id)
            results = requests.get(request_url, headers=self.header)
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. Wrong API Key')
            if results.status_code == 406:
                raise StatusExeception('File has a NON SUCCESS status')
            if results.status_code == 404:
                raise NotFound('File with given ID does not exist: {}'.format(self.file_id))
            if requests.codes.ok:
                resp = results.json()
                resp.update({'status': 1})
                return resp
            results.raise_for_status()
        except AuthenticationFailed as ae:
            self.logger.error('{}'.format(ae))
            return {'url': None}
        except StatusExeception as se:
            self.logger.error('{}'.format(se))
            return {'url': 1}
        except NotFound as nf:
            self.logger.error('{}'.format(nf))
            return {'url': None}
        except ValidationError as ve:
            self.logger.error('Validation error: {}'.format(ve))
            return
        except requests.exceptions.RequestException as er:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: {}'.format(results.status_code))
            self.logger.debug('Response is: {content}'.format(content=er.response.content))

    def save_report(self, out_file=None, out_dir=None, block_size=8192):
        """Save file for given url to disk."""
        def _download_helper(response, out_f, file_size):
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
                    raise NotFoundException('Distination directory does not exist: {}'.format(out_dir))
            else:
                out_dir = os.getcwd()
            url = self.get_report_url()['url']
            if not url:
                raise Exception('Empty report Url recieved')
            if url == 1:
                raise NotFoundException('Report can not be generated for file with NON SUCCESS status.')
            parsed_url = urlparse(url)
            _, file_name = split(parsed_url.path)
            if out_file:
                out_file = expanduser(normpath(out_file))
                out_dir, file_name = split(out_file)

            _, extension = splitext(file_name)
            file_name = file_name if extension == '.zip' else join(file_name + '.zip')
            out_file = join(out_dir, file_name)
            if isfile(out_file):
                raise FileExistsException('Distination File exists: {}'.format(out_file))
            with open(out_file, "wb") as output:
                with urllib.request.urlopen(url) as response:
                    file_size = int(response.getheader("Content-Length"))
                    _download_helper(response, output, file_size)

            return ({'status': 1, 'saved_report': out_file})
        except AuthenticationFailed as ae:
            self.logger.error('{}'.format(ae))
            return {'status': 0, 'message': ae}
        except NotFoundException as nfe:
            self.logger.error('{}'.format(nfe))
            return {'status': 0, 'message': nfe}
        except FileExistsException as fe:
            self.logger.error('{}'.format(fe))
            return {'status': 0, 'message': fe}
        except Exception as ex:
            self.logger.error('Error occured during save report: {}'.format(ex))
            return {'status': 0, 'message': ex}
