"""Representation of Workflow."""
import logging
import requests
from requests.exceptions import RequestException

from cosmosid.helpers.exceptions import CosmosidConnectionError, CosmosidServerError, AuthenticationFailed

LOGGER = logging.getLogger(__name__)


class Workflow(object):
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    def get_workflows(self):
        
        try:
            res = requests.get(
                f"{self.base_url}/api/workflow/v1/workflows",
                params={"enabled": "true"},
                headers=self.header,
            )
        except RequestException:
            raise CosmosidConnectionError()
            
        if not res.ok:
            if res.status_code in (401, 403):
                raise AuthenticationFailed()
            elif 500<=res.status_code<600:
                raise CosmosidServerError()
            else:
                raise CosmosidConnectionError()

        return res.json()
