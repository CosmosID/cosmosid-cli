"""Representation of Artifacts."""

import logging
import os
import uuid
from os.path import isfile, split, splitext
from urllib.parse import urlparse

import requests
from cosmosid.api.files import Runs
from cosmosid.helpers.exceptions import (
    CosmosidException,
    FileExistsException,
)
from cosmosid.utils import progress

LOGGER = logging.getLogger(__name__)


class Artifacts(object):
    """Runs artifact interface."""

    __get_all_artifacts = "api/metagenid/v1/runs/{run_id}/artifacts"
    __get_one_artifact = "api/metagenid/v1/runs/{run_id}/artifacts/{artifact_type}"

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.logger = LOGGER
        self.header = {"X-Api-Key": api_key}
        self.get_one_endpoint = f"{self.base_url}/{self.__get_one_artifact}"
        self.get_all_endpoint = f"{self.base_url}/{self.__get_all_artifacts}"
        self.runs = Runs(base_url=self.base_url, api_key=self.header["X-Api-Key"])

    def get_artifacts(self, run_id):
        request_url = self.get_all_endpoint.format(run_id=run_id)
        results = requests.get(request_url, headers=self.header)
        return results.json()

    def get_artifacts_by_run_id(self, run_id, artifact_type):
        request_url = self.get_one_endpoint.format(
            run_id=run_id, artifact_type=artifact_type
        )
        single_run_meta = self.runs.get_single_run(run_id)
        if not single_run_meta:
            raise CosmosidException(
                f"Response from service is empty for run id {run_id}"
            )
        results = requests.get(request_url, headers=self.header)
        return results.json()

    def save_artifacts(self, url, output_file, output_dir, chunk_size=8192):
        # TODO: exception handling
        r = requests.get(url, stream=True)
        total_size = r.headers["content-length"]
        if output_file:
            file_name, _ = splitext(output_file)
            output_file = f"{file_name}.zip"
        if not output_file:
            parsed_url = urlparse(url)
            _, output_file = split(parsed_url.path)
            output_file = f'{str(uuid.uuid4())[:8]}-{output_file}'
        if not output_dir:
            output_dir = os.getcwd()
        file_full_path = f"{output_dir}/{output_file}"
        if isfile(file_full_path):
            raise FileExistsException(f"Destination File exists: {file_full_path}")
        with open(file_full_path, "wb") as f:
            for i, chunk in enumerate(r.iter_content(chunk_size=chunk_size)):
                progress(i * chunk_size, total_size, "Downloading...")
                f.write(chunk)
            progress(1, 1, "Completed.           \n")
        return file_full_path

    def get_list(self, run_id=None, artifact_type=None):

        if artifact_type and run_id:
            return self.get_artifacts_by_run_id(
                run_id=run_id, artifact_type=artifact_type
            )
        if run_id:
            return self.get_artifacts(run_id=run_id)
