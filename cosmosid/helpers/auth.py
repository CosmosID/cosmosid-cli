"""Functions for Auth."""
import json
import os
import logging
import cosmosid.utils as utils


class ApiKeyAuth(object):
    """Automatic authentication.

    Credential file ~/.cosmosid with the API Key should be created and
    accessable. File format:
        {"api_key": "<your api key string>"}
    """
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
            self.logger.error('Credentials file %s does not exist',
                              utils.collapse_path(api_key_file))
            return None
        try:
            with open(api_key_file, mode='r') as api_key_file:
                api_key = json.load(api_key_file)
                if 'api_key' not in api_key:
                    self.logger.error('Credentials file %s does not contains '
                                      'api_key',
                                      utils.collapse_path(api_key_file))
                    return None
                return api_key['api_key']
        except Exception:
            self.logger.error("%s credentials file is ''corrupted",
                              utils.collapse_path(api_key_file))
