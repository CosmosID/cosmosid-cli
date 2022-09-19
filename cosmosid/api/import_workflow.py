"""Representation of Import Workflow."""
import json
import logging

from cosmosid.helpers.exceptions import UploadException
from requests import post
from requests.exceptions import JSONDecodeError, RequestException, HTTPError

LOGGER = logging.getLogger(__name__)


class ImportWorkflow(object):
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    def import_workflow(self, workflow_ids, files, file_type, folder_id=None):
        upload_url = self.base_url + "/api/metagenid/v3/import"
        payload = {
            'files': [
                {
                    "metadata": {},
                    "parameters": {},
                    "source": "upload",
                    "folder_id": folder_id,
                    "workflow": workflow_ids,
                    "files": files["files"],
                    "sample_name": files["file_name"],
                    "sample_type": file_type,
                }
            ]
        }
        try:
            response = post(
                upload_url,
                data=json.dumps(payload),
                headers=self.header,

            )
            errors = response.json().get('errors')
            if errors:
                raise UploadException(
                    '\n'.join([
                        f"Error with {error.get('sample', {}).get('sample_name')}: {error.get('description')}"
                        for error in errors
                    ])
                )
            response.raise_for_status()
        except HTTPError as err:
            self.logger.error(f"{files} files can't be uploaded. Aborting.")
            raise RuntimeError(err)
        except RequestException as err:
            self.logger.error("Upload request can't be send", err)
            raise RequestException(err)
        except JSONDecodeError as err:
            raise RequestException(err)
