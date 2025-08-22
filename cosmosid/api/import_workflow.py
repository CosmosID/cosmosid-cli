"""Representation of Import Workflow."""

import copy
import json
import logging

from requests import post
from requests.exceptions import JSONDecodeError, RequestException, HTTPError
from cosmosid.enums import Workflows

LOGGER = logging.getLogger(__name__)


LONG_READ_WORKFLOWS = [
    Workflows.LongRead16s18sPackage,
    Workflows.LongRead16s18sGreengenes2Amplicon,
    Workflows.LongRead16s18sSilvaAmplicon,
    Workflows.LongRead16s18sGtdbSsu220Amplicon,
    Workflows.LongRead16s18sEmuDefaultAmplicon,
    Workflows.LongRead16s18sMidasAmplicon,
    Workflows.LongRead16s18sHomdAmplicon,
    Workflows.LongReadItsAmplicon,
    Workflows.FullLengthRrnaAmplicon,
]

WORKFLOW_TO_DATABASE = {
    Workflows.LongRead16s18sGreengenes2Amplicon: "long_read_greengenes2",
    Workflows.LongRead16s18sSilvaAmplicon: "long_read_silva",
    Workflows.LongRead16s18sGtdbSsu220Amplicon: "long_read_gtdb_ssu_220",
    Workflows.LongRead16s18sEmuDefaultAmplicon: "long_read_emu_default",
    Workflows.LongRead16s18sMidasAmplicon: "long_read_midas",
    Workflows.LongRead16s18sHomdAmplicon: "long_read_homd",
    Workflows.LongReadItsAmplicon: "long_read_unite",
    Workflows.FullLengthRrnaAmplicon: "long_read_rrn",
}


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
        forward_primer=None,
        reverse_primer=None,
        long_read_params=None,
    ):
        upload_url = f"{self.base_url}/api/workflow/v1/workflows/{Workflows.BatchImport}/start"

        workflows = workflow_ids.copy()
        workflows_with_parameters = {}
        long_read_workflows = {}
        if Workflows.AmpliseqBatchGroup in workflows:
            workflows.remove(Workflows.AmpliseqBatchGroup)
            workflows_with_parameters[Workflows.AmpliseqBatchGroup] = {
                "forward_primer": forward_primer,
                "reverse_primer": reverse_primer,
            }

        for workflow in LONG_READ_WORKFLOWS:
            if workflow in workflows:
                params = copy.copy(long_read_params)
                if workflow != Workflows.LongRead16s18sPackage:
                    keys_to_remove = []
                    for param in params:
                        if param.startswith("long_read_"):
                            keys_to_remove.append(param)
                    for key in keys_to_remove:
                        params.pop(key)
                    params["database"] = WORKFLOW_TO_DATABASE[workflow]
                long_read_workflows[workflow] = params

        parameters = {
            "workflows": long_read_workflows or {},
        }
        if host_name:
            parameters["host_name"] = host_name
        payload = {
            "import_params_list": [
                {
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
                    "sample_system_metadata": [],
                }
                for pair in pairs
            ],
            "workflows": workflows_with_parameters,
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
