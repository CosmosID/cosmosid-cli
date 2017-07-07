"""Representation of Analysis."""
import requests
from base64 import b64encode
from metagen.helpers.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)


class Analysis(object):
    _resource_path = '/api/metagenid/v1/files/{file_id}/analysis'

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = logger
        self.header = {'X-Api-Key': api_key}

    def get_list(self, file_id=None):
        request_url = "{}{}".format(self.base_url, self.__class__._resource_path)
        request_url = request_url.format(file_id=file_id)

        data = {}
        resut_data = {}
        try:
            results = requests.get(request_url, headers=self.header, json=data)
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. Wrong API Key.')
            if results.status_code == 404:
                resut_data = results.json()
                resut_data.update({'status': 0})
                return resut_data
            if requests.codes.ok:
                resut_data = results.json()
                resut_data.update({'status': 1})
                return resut_data
            results.raise_for_status()
        except AuthenticationFailed as ae:
            self.logger.error('{}'.format(ae))
        except requests.exceptions.RequestException as er:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: {}'.format(results.status_code))
            self.logger.debug('Response is: {content}'.format(content=er.response.content))
