"""Representation of Import Workflow."""
import json
import logging

from requests import post
from requests.exceptions import JSONDecodeError, RequestException, HTTPError
from cosmosid.enums import Workflows

LOGGER = logging.getLogger(__name__)


class ImportWorkflow(object):
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    def import_workflow(self, workflow_ids, pairs, file_type, folder_id=None, host_name=None, forward_primer=None, reverse_primer=None):
        upload_url = f'{self.base_url}/api/workflow/v1/workflows/{Workflows.BatchImport}/start'
        
        workflows = workflow_ids.copy()
        workflows_with_parameters = {}
        if Workflows.AmpliseqBatchGroup in workflows:
            workflows.remove(Workflows.AmpliseqBatchGroup)
            workflows_with_parameters[Workflows.AmpliseqBatchGroup] = {
                "forward_primer": forward_primer,
                "reverse_primer": reverse_primer,
            }
            
        parameters = {
            "workflows": {},
        }
        if host_name:
            parameters["host_name"] = host_name
        
        payload = {
            "import_params_list": [{
                "sample_name": pair["file_name"],
                "parent_folder": folder_id,
                "sample_type": file_type,
                "source": "upload",
                "files": pair["files"],
                "metadata": {},
                "parameters": parameters,
                "workflows": workflows,
                "sample_tags": [],
                "sample_custom_metadata": [],
                "sample_system_metadata": []
            } for pair in pairs],
            "workflows": workflows_with_parameters
        }
        try:
            response = post(
                upload_url,
                data=json.dumps(payload),
                headers=self.header,
            )
            response.raise_for_status()
        except HTTPError as err:
            self.logger.error(f"{pairs} files can't be uploaded. Aborting.")
            raise RuntimeError(err)
        except RequestException as err:
            self.logger.error("Upload request can't be send", err)
            raise RequestException(err)
        except JSONDecodeError as err:
            raise RequestException(err)
