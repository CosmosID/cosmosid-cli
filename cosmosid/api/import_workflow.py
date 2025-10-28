"""Representation of Import Workflow."""

import json
import logging

from requests import post
from requests.exceptions import RequestException, HTTPError
from cosmosid.enums import Workflows

LOGGER = logging.getLogger(__name__)


class ImportWorkflow(object):
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    def import_workflow(
        self,
        workflow_ids,
        pairs,
        file_type,
        folder_id=None,
        host_name=None,
        workflow_parameters=None,
    ):
        upload_url = f"{self.base_url}/api/workflow/v1/workflows/{Workflows.BatchImport}/start"

        # Build per-sample parameters structure
        sample_parameters = {
            "workflows": workflow_parameters or {},
        }
        if host_name:
            sample_parameters["host_name"] = host_name

        payload = {
            "import_params_list": [
                {
                    "sample_name": pair["file_name"],
                    "parent_folder": folder_id,
                    "sample_type": file_type,
                    "source": "upload",
                    "files": pair["files"],
                    "metadata": {},
                    "parameters": sample_parameters,
                    "workflows": workflow_ids,  # ALL workflows go in the per-sample workflows list
                    "sample_tags": [],
                    "sample_custom_metadata": [],
                    "sample_system_metadata": [],
                }
                for pair in pairs
            ],
            "workflows": {},  # Top-level workflows for workflows without parameters (typically empty)
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
