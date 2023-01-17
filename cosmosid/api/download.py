"""
Representation of folder structure.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.util import find_spec
from logging import getLogger
from os.path import join
from typing import List, Tuple

from requests import post

from cosmosid.api.auth import get_profile
from cosmosid.config import CHUNK_SIZE, CONCURRENT_DOWNLOADS
from cosmosid.helpers.downloader import Downloader
from cosmosid.helpers.exceptions import CosmosidException
from cosmosid.helpers.thread_logger import ThreadLogger

logger = getLogger(__name__)


class SamplesDownloader:
    """Samples structure."""

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.auth_header = {"X-Api-Key": api_key}
        self.original_file = (
            "{self.base_url}/api/metagenid/v3/users/{user_uuid}/download"
        )
        self.check_pycurl()

    @staticmethod
    def check_pycurl():
        if not find_spec("pycurl"):
            logger.warning(
                """The "PyCurl" is not found.
We recommend installing pycurl for the best experience with a sample download, see: http://pycurl.io/docs/latest/index.html#installation"""
            )

    def get_sample_data(self, samples_ids) -> dict:
        user_profile = get_profile(base_url=self.base_url, headers=self.auth_header)
        request_url = (
            f"{self.base_url}/api/metagenid/v3/users/{user_profile['id']}/download"
        )
        response = post(
            request_url,
            headers=self.auth_header,
            json={"samples": samples_ids, "notification": "false"},
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_errors(data) -> List[dict]:
        errors = []
        for error in data.get("errors", []):
            if error not in errors:
                errors.append(error)
        return errors

    @staticmethod
    def get_available_samples(samples, errors) -> List[dict]:
        result = samples.copy()
        for error in errors:
            for sample in samples:
                if error["sample_id"] == sample:
                    result.remove(sample)
        return result

    @classmethod
    def handle_data(cls, data) -> Tuple[List[str], List[dict]]:
        if not data:
            return ["No data"], []

        errors = cls.get_errors(data)
        samples = cls.get_available_samples(data.get("samples"), errors)

        errors_texts = ["{error} ({sample_id})".format(**error) for error in errors]

        if not samples:
            return errors_texts, []

        files = [
            {
                "file_name": file["file_name"],
                "url": file["url"],
                "size": file["size"],
            }
            for sample in samples
            for file in sample.get("files", [])
        ]
        return errors_texts, files

    @staticmethod
    def download_sample(file, output_dir, display_loading):
        thread_logger = ThreadLogger()
        try:
            Downloader.load_file(
                file["url"],
                file["size"],
                file["file_name"],
                output_dir,
                CHUNK_SIZE,
                display_loading,
            )
            return join(output_dir, file["file_name"])
        except Exception as error:
            thread_logger.info(file["file_name"], str(error).strip())

    def download_samples(
        self, samples_ids, output_dir, concurrent_downloads, display_loading=True
    ):
        try:
            data = self.get_sample_data(samples_ids)
            errors, files = self.handle_data(data)
            for error in errors:
                logger.error(error)
            if not files:
                return
            if display_loading:
                ThreadLogger().start()
            else:
                logger.info("Loading..")
            files_paths = []
            with ThreadPoolExecutor(
                max_workers=concurrent_downloads or CONCURRENT_DOWNLOADS
            ) as executor:
                future_to_url = {
                    executor.submit(
                        self.download_sample, file, output_dir, display_loading
                    ): file
                    for file in files
                }
                for future in as_completed(future_to_url):
                    error = future.exception(1)
                    if error is None:
                        filepath = future.result()
                        if filepath:
                            files_paths.append(filepath)
                    else:
                        logger.error(error)
            if display_loading:
                ThreadLogger().stop()
            return files_paths
        except CosmosidException as error:
            if display_loading:
                ThreadLogger().stop()
            raise CosmosidException(f"{error}") from error
