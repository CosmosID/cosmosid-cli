"""
Representation of folder structure
"""
import requests
from base64 import b64encode
import json
from cosmosid.helpers.exceptions import AuthenticationFailed, NotFound
import logging

logger = logging.getLogger(__name__)


class Files(object):
    _resource_path = '/api/metagenid/v1/files'

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = logger
        self.auth_header = {'X-Api-Key': api_key}
        self.request_url = '{}{}'.format(self.base_url, self.__class__._resource_path)

    def get_list(self, parent_id=None):

        data = {'folder_id': parent_id} if parent_id else {}
        results = {}
        try:
            results = requests.get(self.request_url, headers=self.auth_header, params=data)
            if results.status_code == 400:
                if json.loads(results.text)['error_code'] == 'NotUUID':
                    raise NotFound('Wrong ID.')
            if results.status_code == 404:
                results = results.json()
                results.update({'status': 0})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. Wrong API Key.')
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                results.update({'status': 1})
                return results
        except AuthenticationFailed as ae:
            self.logger.error('{}'.format(ae))
        except NotFound as nf:
            self.logger.error('{}'.format(nf))
        except requests.exceptions.RequestException as er:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: {}'.format(results.status_code))
            self.logger.debug('Response is: {content}'.format(content=er.response.content))

    def get_file(self, file_id=None):

        request_url = self.request_url + "/" + file_id
        results = {}
        try:
            results = requests.get(request_url, headers=self.auth_header)
            if results.status_code == 400:
                if json.loads(results.text)['error_code'] == 'NotUUID':
                    raise NotFound('Wrong ID.')
            if results.status_code == 404:
                results = results.json()
                results.update({'status': 0})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. Wrong API Key.')
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                results.update({'status': 1})
                return results
        except AuthenticationFailed as ae:
            self.logger.error('{}'.format(ae))
        except NotFound as nf:
            self.logger.error('{}'.format(nf))
        except requests.exceptions.RequestException as er:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: {}'.format(results.status_code))
            self.logger.debug('Response is: {content}'.format(content=er.response.content))
