import os
import requests


class BaseApi(object):

    def __init__(self, **kwargs):
        self.base_url = kwargs['base_url']
        self.api_key = kwargs['api_key']

    def session(self):
        session = requests.Session()
        session.setHeader({'X-Api-Key': self.api_key})
        return session
