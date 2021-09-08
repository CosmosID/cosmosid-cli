"""Representation of Import Workflow."""
import logging
import requests
import json

from requests import RequestException

LOGGER = logging.getLogger(__name__)


class ImportWorkflow(object):

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {'X-Api-Key': api_key, "Content-Type": "application/json"}

    def import_workflow(self, workflow_ids, files, file_type, folder_id=None):
        upload_url = self.base_url + "/api/metagenid/v3/import"
        payload = {}
        payload['files'] = []
        payload_dict = {'metadata': {}, 'parameters': {}, 'source': 'upload', 'folder_id': folder_id,
                        'workflow': workflow_ids, 'files': files['files'],
                        'sample_name': files['file_name'],
                        "sample_type": file_type}
        payload['files'].append(payload_dict)
        try:
            response = requests.post(
                upload_url,
                data=json.dumps(payload),
                headers=self.header,)
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"{files} files can't be uploaded. Aborting.")
            raise RuntimeError(e)
        except RequestException as err:
            print("Upload request can't be send", err)
            raise RequestException(err)