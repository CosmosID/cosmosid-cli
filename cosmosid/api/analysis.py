"""Representation of Analysis."""
import logging

import requests
from cosmosid.api.files import Runs
from cosmosid.helpers.exceptions import (AuthenticationFailed,
                                         CosmosidException,
                                         NotFoundException)

LOGGER = logging.getLogger(__name__)


class Analysis(object):
    """Runs analysis interface."""
    __resource_path = '/api/metagenid/v1/runs/{run_id}/analysis'

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {'X-Api-Key': api_key}
        self.request_url = "{}{}".format(self.base_url, self.__resource_path)
        self.runs = Runs(base_url=self.base_url,
                         api_key=self.header['X-Api-Key'])

    def __is_runid_in_file(self, run_id, file_id):
        """Get given run meta and check is the run in sample."""
        single_run = self.runs.get_single_run(run_id)
        if single_run:
            if single_run['status']:
                if single_run['file']['id'] == file_id:
                    return True
        return False

    def __get_analysis_by_file_id(self, file_id):
        last_run = self.runs.get_last_run_for_file(file_id)
        result_data = None
        if last_run:
            result_data = self.__get_analysis_by_run_id(last_run['id'])
        return result_data

    def __get_analysis_by_run_id(self, run_id):
        request_url = self.request_url.format(run_id=run_id)
        try:
            single_run_meta = self.runs.get_single_run(run_id)
            if not single_run_meta:
                raise CosmosidException('Response from service is empty for '
                                        'run id %s' % run_id)
            if not single_run_meta['status']:
                raise NotFoundException(single_run_meta['message'])

            results = requests.get(request_url, headers=self.header)
            if results.status_code == 403:
                raise AuthenticationFailed('Authentication Failed. '
                                           'Wrong API Key.')
            if results.status_code == 404:
                result_data = results.json()
                result_data.update({'status': 0})
                result_data.update({'run_meta': single_run_meta})
                return result_data
            if requests.codes.ok:
                result_data = results.json()
                result_data.update({'status': 1})
                result_data.update({'run_meta': single_run_meta})
                return result_data
            results.raise_for_status()
        except AuthenticationFailed:
            self.logger.error('Authentication Failed')
        except NotFoundException:
            self.logger.error('Not Found')
        except CosmosidException:
            self.logger.error('Got Analysis data exception.')
        except requests.exceptions.RequestException:
            self.logger.debug('Debug', exc_info=True)
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: %s', results.status_code)

    def get_list(self, file_id=None, run_id=None):
        """Get analysis data.

        cli analysis --id ID
        """
        if file_id and run_id:
            if self.__is_runid_in_file(run_id, file_id):
                return self.__get_analysis_by_run_id(run_id)
            msg = 'File %s does not contain Run %s' % (self.file_id,
                                                       self.run_id)
            return {'status': 0,
                    'message': msg}
        elif run_id and not file_id:
            return self.__get_analysis_by_run_id(run_id)
        elif file_id and not run_id:
            return self.__get_analysis_by_file_id(file_id)
