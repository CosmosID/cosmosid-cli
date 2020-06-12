"""
Representation of folder structure.
"""
import json
import logging
from operator import itemgetter

import requests

import cosmosid.utils as utils
from cosmosid.helpers.exceptions import (AuthenticationFailed,
                                         CosmosidException, NotFound,
                                         NotFoundException)

LOGGER = logging.getLogger(__name__)


class Files(object):
    """Files tructure."""
    __resource_path = '/api/metagenid/v2/files'

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.auth_header = {'X-Api-Key': api_key}
        self.request_url = '{}{}'.format(self.base_url,
                                         self.__class__.__resource_path)

    def get_list(self, parent_id=None):

        data = {'folder_id': parent_id} if parent_id else {}
        results = {}
        try:
            results = requests.get(self.request_url,
                                   headers=self.auth_header,
                                   params=data)
            if results.status_code == 400:
                if json.loads(results.text)['error_code'] == 'NotUUID':
                    raise NotFound('Wrong ID.')
            if results.status_code == 404:
                results = results.json()
                results.update({'status': 0})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key.')
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                results.update({'status': 1})
                #microbiom standart doesnt have an export TODO:export var
                results['items'] = [i for i in results['items']
                                    if i['content_type'] != 7]
                return results
        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error('Error occured during request')
            utils.log_traceback(err)

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
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key.')
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()['items'].pop()
                results.update({'status': 1})
                return results
        except AuthenticationFailed as err:
            self.logger.error('AuthenticationFailed')
            utils.log_traceback(err)
        except NotFound as err:
            self.logger.error('Not Found')
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: %s', results.status_code)
            utils.log_traceback(err)


class Runs(Files):
    __resource_path = '/api/metagenid/v1/files/{file_id}/runs'
    __single_run_path = '/api/metagenid/v1/runs/{run_id}'

    def get_last_run_for_file(self, file_id):
        try:
            runs_list = self.get_runs_list(file_id=file_id)
            if not runs_list:
                raise CosmosidException('Error occurred on get list of runs '
                                        'for a File: {}'.format(file_id))
            if not runs_list['status']:
                raise NotFoundException(runs_list['message'])

            sorted_runs_list = sorted(runs_list['runs'],
                                      key=itemgetter('created'),
                                      reverse=True)
            return sorted_runs_list[0]
        except NotFoundException as err:
            self.logger.error('NotFound')
            utils.log_traceback(err)
        except CosmosidException:
            self.logger.error('Runs list exception.')
            return None
        except Exception as err:
            self.logger.error('Client exception occured')
            utils.log_traceback(err)

    def get_single_run(self, run_id):
        run_metadata_url = "{}{}".format(
            self.base_url,
            self.__single_run_path.format(run_id=run_id))
        results = {}
        try:
            results = requests.get(run_metadata_url, headers=self.auth_header)
            if results.status_code == 400:
                if json.loads(results.text)['error_code'] == 'NotUUID':
                    raise NotFound('Wrong ID.')
            if results.status_code == 404:
                results = results.json()
                results.update({'status': 0})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key.')
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                results.update({'status': 1})
                return results
        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: %s', results.status_code)
            utils.log_traceback(err)

    def get_runs_list(self, file_id=None):
        sample_runs_url = "{}{}".format(
            self.base_url,
            self.__resource_path.format(file_id=file_id))
        results = {}

        try:
            file_metadata = self.get_file(file_id)
            if not file_metadata:
                raise CosmosidException('Response from service is empty '
                                        'for file id {}'.format(file_id))
            if not file_metadata['status']:
                raise NotFoundException(file_metadata['message'])
            results = requests.get(sample_runs_url, headers=self.auth_header)
            if results.status_code == 400:
                if json.loads(results.text)['error_code'] == 'NotUUID':
                    raise NotFound('Wrong ID.')
            if results.status_code == 404:
                results = results.json()
                results.update({'status': 0})
                results.update({'file_name': file_metadata['name']})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key.')
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                results.update({'status': 1})
                results.update({'file_name': file_metadata['name']})
                return results
        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: %s', results.status_code)
            utils.log_traceback(err)
        except NotFoundException as err:
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error('Got runs list exception')
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error('Client exception occured')
            utils.log_traceback(err)
