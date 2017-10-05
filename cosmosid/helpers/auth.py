"""Functions for Auth."""
import json
import os
import logging
import cosmosid.utils as utils


class ApiKeyAuth(object):

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.api_key = None
        self.header = {'X-Api-Key': self.api_key}

    def __call__(self):
        api_key = self._get_api_key()
        if api_key:
            self.api_key = api_key
        return self.api_key

    def _get_api_key(self):
        api_key_file = os.path.expanduser('~/.cosmosid')
        api_key = {}
        if not os.path.exists(api_key_file):
            self.logger.error('Credentials file {} does not exist'
                              .format(utils.collapse_path(api_key_file)))
            return None
        try:
            with open(api_key_file, mode='r') as f:
                api_key = json.load(f)
                if 'api_key' not in api_key:
                    self.logger.error('Credentials file {} does not contains api_key'
                                      .format(utils.collapse_path(api_key_file)))
                    return None
                return api_key['api_key']
        except Exception:
            self.logger.error("{} credentials file is corrupted".format(utils.collapse_path(api_key_file)))
