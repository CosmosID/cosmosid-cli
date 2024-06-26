"""
Representation of folder structure.
"""
import json
import logging
from operator import itemgetter

import requests

import cosmosid.utils as utils
from cosmosid.helpers.exceptions import (
    AuthenticationFailed,
    CosmosidException,
    NotFound,
    NotFoundException,
)

LOGGER = logging.getLogger(__name__)

class Files(object):
    """Files structure."""

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.logger = LOGGER
        self.auth_header = {"X-Api-Key": api_key}
        self.request_url = f"{self.base_url}/api/metagenid/v3/dashboard"
        self.request_url_files = f"{self.base_url}/api/metagenid/v2/files"

    def get_dashboard(self, parent_id):
        params = {}
        if parent_id:
            params["folder_id"] = parent_id
        result = {"items": [], "total": 0, "status": 1}
        result_set = False
        try:
            response = requests.get(
                self.request_url, headers=self.auth_header, params=params
            )
            if response.status_code == 400:
                content = json.loads(response.text)
                if content["error_code"] == "NotUUID":
                    raise NotFound("Invalid ID specified.")

            if response.status_code == 404:
                result = response.json()
                result.update({"status": 0})
                return result

            if response.status_code == 403:
                raise AuthenticationFailed(
                    "Authentication Failed. Wrong API Key.")

            response.raise_for_status()

            if requests.codes.ok:
                content = response.json()
                if not result_set:
                    result["status"] = 1
                    result["is_public"] = content["is_public"]
                result["items"].extend(content["files"])
                result["total"] += len(content["files"])

            return result

        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error("Error occurred during request")
            utils.log_traceback(err)

    def get_list(self, parent_id=None, limit=1000):
        params = {"limit": limit, "offset": 0}
        if parent_id:
            params["folder_id"] = parent_id
        result = {"items": [], "total": 0, "status": 1}
        result_set = False
        try:
            while True:
                response = requests.get(
                    self.request_url_files, headers=self.auth_header, params=params
                )
                if response.status_code == 400:
                    content = json.loads(response.text)
                    if content["error_code"] == "NotUUID":
                        raise NotFound("Invalid ID specified.")

                if response.status_code == 404:
                    result = response.json()
                    result.update({"status": 0})
                    return result

                if response.status_code == 403:
                    raise AuthenticationFailed(
                        "Authentication Failed. Wrong API Key.")

                response.raise_for_status()

                if requests.codes.ok:
                    content = response.json()
                    if not result_set:
                        result["status"] = 1
                        result["name"] = content["name"]
                        result["is_public"] = content["is_public"]
                        result["breadcrumbs"] = content["breadcrumbs"]
                    # microbiom standard doesn't have an export
                    items = [i for i in content["items"]
                             if i["content_type"] != 7]
                    result["items"].extend(items)
                    result["total"] += len(items)
                    if content["total"] < limit:
                        break
                    params["offset"] += limit
            return result

        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error("Error occurred during request")
            utils.log_traceback(err)

    def get_file(self, file_id=None):
        request_url = self.request_url_files + \
            (f"/{file_id}" if file_id else "")
        results = {}
        try:
            results = requests.get(request_url, headers=self.auth_header)
            if (
                results.status_code == 400
                and json.loads(results.text)["error_code"] == "NotUUID"
            ):
                raise NotFound("Wrong ID.")
            if results.status_code == 404:
                results = results.json()
                results.update({"status": 0})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed(
                    "Authentication Failed. Wrong API Key.")
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()["items"].pop()
                results.update({"status": 1})
                return results
        except AuthenticationFailed as err:
            self.logger.error("AuthenticationFailed")
            utils.log_traceback(err)
        except NotFound as err:
            self.logger.error("Not Found")
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error("Error occurred during request")
            self.logger.error("Response Status Code: %s", results.status_code)
            utils.log_traceback(err)

    def make_dir(self, name, parent_id=None):
        """
        Create a new folder in the parent folder.
        :param name: name of the new folder
        :param parent_id: parent folder id (default is root)
        :return: created folder id
        """
        request_url = f"{self.base_url}/api/metagenid/v1/files"
        if parent_id is None:
            parent_id = 0 # to make falsy value
        data = {"type": 1, "parent": parent_id, "name": name}
        try:
            response = requests.post(
                request_url, headers=self.auth_header, json=data
            )
        except requests.exceptions.RequestException as err:
            self.logger.error("Error occurred during request")
            utils.log_traceback(err)
            raise CosmosidException("Error occurred during folder creation.")
        if response.status_code == 201:
            response_data = response.json()
            # V1 always return a list of created items
            return response_data["created"][0]
        if response.status_code == 403:
            raise AuthenticationFailed(
                "Not Authorized, check credentials.")
        if response.status_code == 404:
            raise NotFound(f"Parent folder:{parent_id} is not found.")
        
        raise CosmosidException(
                        "Error occurred during folder creation.")

class Runs(Files):
    __resource_path = "/api/metagenid/v1/files/{file_id}/runs"
    __single_run_path = "/api/metagenid/v1/runs/{run_id}"

    def get_last_run_for_file(self, file_id):
        try:
            runs_list = self.get_runs_list(file_id=file_id)
            if not runs_list:
                raise CosmosidException(
                    f"Error occurred on get list of runs for a File: {file_id}"
                )

            if not runs_list.get("status"):
                raise NotFoundException(runs_list["message"])

            sorted_runs_list = sorted(
                runs_list["runs"], key=itemgetter("created"), reverse=True
            )
            return sorted_runs_list[0]
        except NotFoundException as err:
            self.logger.error("NotFound")
            utils.log_traceback(err)
        except CosmosidException:
            self.logger.error("Runs list exception.")
            return None
        except Exception as err:
            self.logger.error("Client exception occurred")
            utils.log_traceback(err)

    def get_single_run(self, run_id):
        run_metadata_url = (
            f"{self.base_url}{self.__single_run_path.format(run_id=run_id)}"
        )

        results = {}
        try:
            results = requests.get(run_metadata_url, headers=self.auth_header)
            if (
                results.status_code == 400
                and json.loads(results.text)["error_code"] == "NotUUID"
            ):
                raise NotFound("Wrong ID.")
            if results.status_code == 404:
                results = results.json()
                results.update({"status": 0})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed(
                    "Authentication Failed. " "Wrong API Key.")
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                results.update({"status": 1})
                return results
        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error("Error occurred during request")
            self.logger.error("Response Status Code: %s", results.status_code)
            utils.log_traceback(err)

    def get_runs_list(self, file_id=None):
        sample_runs_url = (
            f"{self.base_url}{self.__resource_path.format(file_id=file_id)}"
        )

        results = {}

        try:
            file_metadata = self.get_file(file_id)
            if not file_metadata:
                raise CosmosidException(
                    f"Response from service is empty for file id {file_id}"
                )

            if not file_metadata.get("status"):
                raise NotFoundException(file_metadata["message"])
            results = requests.get(sample_runs_url, headers=self.auth_header)
            if (
                results.status_code == 400
                and json.loads(results.text)["error_code"] == "NotUUID"
            ):
                raise NotFound("Wrong ID.")
            if results.status_code == 404:
                results = results.json()
                results.update({"status": 0})
                results.update({"file_name": file_metadata["name"]})
                return results
            if results.status_code == 403:
                raise AuthenticationFailed(
                    "Authentication Failed. Wrong API Key.")
            results.raise_for_status()
            if requests.codes.ok:
                results = results.json()
                if results:
                    file_name = ""
                    for index, run in enumerate(results["runs"]):
                        run_url = f"{self.base_url}{self.__single_run_path.format(run_id=run['id'])}"
                        run_results = requests.get(run_url, headers=self.auth_header)
                        run_results = run_results.json()
                        if run_results["workflows"]["name"] in ("import",):
                            del results["runs"][index]
                        run["workflow_name"] = run_results["workflows"]["name"]
                        run["workflow_version"] = run_results["workflows"]["version"]
                        run["artifact_types"] = ",".join(run_results["artifacts"])
                        if not file_name:
                            file_name = run_results["file"]["name"]
                        results["file_name"] = file_name
                    return results

                results.update({"status": 1})
                results.update({"file_name": file_metadata["name"]})
                return results
        except AuthenticationFailed as err:
            utils.log_traceback(err)
        except NotFound as err:
            utils.log_traceback(err)
        except requests.exceptions.RequestException as err:
            self.logger.error("Error occurred during request")
            self.logger.error("Response Status Code: %s", results.status_code)
            utils.log_traceback(err)
        except NotFoundException as err:
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error("Got runs list exception")
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error("Client exception occurred")
            utils.log_traceback(err)
