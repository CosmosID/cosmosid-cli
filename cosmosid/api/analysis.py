"""Representation of Analysis."""
import requests
from base64 import b64encode
from cosmosid.helpers.exceptions import AuthenticationFailed, NotFoundException, CosmosidException
from cosmosid.api.files import Files
import logging

logger = logging.getLogger(__name__)
content_type_map = {'1': 'Folder',
                    '2': 'Metagenomics Sample',
                    '3': 'MRSA Sample',
                    '4': 'Listeria Sample',
                    '5': 'Amplicon 16S Sample'
                    }
allowed_content_type = ['2', '3', '4']


class Analysis(object):
    _resource_path = '/api/metagenid/v1/files/{file_id}/analysis'

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = logger
        self.header = {'X-Api-Key': api_key}
        self.request_url = "{}{}".format(self.base_url, self.__class__._resource_path)

    def get_list(self, file_id=None):
        request_url = self.request_url.format(file_id=file_id)
        fo = Files(base_url=self.base_url, api_key=self.header['X-Api-Key'])
        data = {}
        resut_data = {}
        try:
            file_data = fo.get_file(file_id=file_id)
            if file_data:
                if not file_data['status']:
                    raise NotFoundException(file_data['message'])
            else:
                raise CosmosidException('Response from service is empty for file id {}'.format(file_id))
            if str(file_data['content_type']) not in allowed_content_type:
                content_type = content_type_map.get(str(file_data['content_type']), "Unknown")
                raise CosmosidException('Getting analysis list for {} is not possible'.format(content_type))
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
        except NotFoundException as nfex:
            self.logger.error('NotFound: {}'.format(nfex))
        except CosmosidException as mex:
            self.logger.error('Get File data exception: {}'.format(mex))
        except requests.exceptions.RequestException as er:
            self.logger.error('Error occured during request')
            self.logger.error('Response Status Code: {}'.format(results.status_code))
            self.logger.debug('Response is: {content}'.format(content=er.response.content))
