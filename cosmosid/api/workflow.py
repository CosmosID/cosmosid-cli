"""Representation of Workflow."""
import logging
import requests

LOGGER = logging.getLogger(__name__)


class Workflow(object):

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {'X-Api-Key': api_key, "Content-Type": "application/json"}

    def get_workflows(self):
        res = requests.get(self.base_url + "/api/workflow/v1/workflows",
                           params={'enabled': 'true'},
                           headers=self.header)
        res.raise_for_status()
        return res.json()
