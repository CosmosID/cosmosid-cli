"""Python client."""

import logging
import sys

import cosmosid.api.upload as upload
import cosmosid.utils as utils
from cosmosid.api import auth
from cosmosid.api.analysis import Analysis
from cosmosid.api.artifacts import Artifacts
from cosmosid.api.download import SamplesDownloader
from cosmosid.api.files import Files, Runs
from cosmosid.api.import_workflow import ImportWorkflow
from cosmosid.api.reports import Reports
from cosmosid.api.workflow import Workflow
from cosmosid.helpers.auth import ApiKeyAuth
from cosmosid.helpers.exceptions import (
    CosmosidException,
    DownloadSamplesException,
    NotFoundException,
    UploadException,
    ValidationError,
)

LOGGER = logging.getLogger(__name__)


class CosmosidApi(object):
    """
    Client is a python client on top of the CosmosID interface.
    """

    logger = logging.getLogger(__name__)

    BASE_URL = "https://app.cosmosid.com"

    def __init__(self, api_key=None, base_url=BASE_URL):
        """Initialize a client with the given params."""
        try:
            if not api_key:
                api_key = self.__auth()
            api_key = utils.key_len(api_key)
        except ValidationError as err:
            utils.log_traceback(err)
        base_url = base_url or self.BASE_URL
        if base_url != self.BASE_URL:
            self.logger.info("Using base URL: %s", base_url)
        self.base_url = base_url
        self.api_key = api_key

    def __auth(self):
        """Read api_key for authentication."""
        api_key = None
        try:
            auth = ApiKeyAuth()
            api_key = auth()
            if api_key is None:
                raise ValidationError("Api Key is empty")
        except (KeyError, ValueError) as err:
            self.logger.info("Can't get Cosmosid Api Key")
            utils.log_traceback(err)
        return api_key

    def dashboard(self, parent):
        file_obj = Files(base_url=self.base_url, api_key=self.api_key)
        try:
            res = file_obj.get_dashboard(parent_id=parent)
            if res:
                if res["status"]:
                    return res
                else:
                    raise NotFoundException(res["message"])
            else:
                raise CosmosidException(
                    "Response from service is empty " "for directory {}".format(parent)
                )
        except NotFoundException as err:
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error("Get directory list exception")
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error("Failed to get listing of directory %s", parent)
            utils.log_traceback(err)

    def get_enabled_workflows(self):
        workflow = Workflow(base_url=self.base_url, api_key=self.api_key)
        try:
            return workflow.get_workflows()
        except Exception as err:
            self.logger.error("Client exception occurred")
            utils.log_traceback(err)

    def import_workflow(self, workflow_ids, files, file_type, parent_id=None):
        import_wf = ImportWorkflow(base_url=self.base_url, api_key=self.api_key)
        files_s3 = []
        try:
            for file in files["files"]:
                files_s3.append(
                    upload.upload_file(
                        file=file,
                        file_type=file_type,
                        parent_id=parent_id,
                        api_key=self.api_key,
                        base_url=self.base_url,
                    )
                )
                self.logger.info(f'\r{file} was uploaded.' + ' ' * 30)

            import_wf.import_workflow(
                workflow_ids,
                {"files": files_s3, "file_name": files["sample_name"]},
                file_type,
                parent_id,
            )
        except UploadException as err:
            self.logger.error("\nError occurred on File import: {}".format(files))
            utils.log_traceback(err)

    def upload_files(self, files, file_type, parent_id=None):
        """Upload single file."""
        error_msg = "\nError occurred on File upload: {}".format(files)
        try:
            upload_res = upload.upload_and_save(
                files=files,
                parent_id=parent_id,
                file_type=file_type,
                base_url=self.base_url,
                api_key=self.api_key,
            )
            if upload_res:
                return upload_res["id"]
            else:
                self.logger.error(error_msg)
        except UploadException as err:
            self.logger.error(error_msg)
            utils.log_traceback(err)

    def analysis_list(self, file_id=None, run_id=None):
        """Get list of analysis for a given file id."""
        if not file_id:
            raise CosmosidException('Wrong file id')
        analysis = Analysis(base_url=self.base_url, api_key=self.api_key)
        try:
            analysis_list = analysis.get_list(file_id=file_id, run_id=run_id)
            if analysis_list:
                if analysis_list["status"]:
                    return analysis_list
                else:
                    raise NotFoundException(analysis_list["message"])
            else:
                raise CosmosidException(
                    "Error occurred on getting list of analysis for a File: %s" % file_id
                )
        except NotFoundException as err:
            self.logger.error("NotFound")
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error("Get analysis list exception")
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error("Client exception occurred")
            utils.log_traceback(err)

    def artifacts_list(
        self,
        run_id=None,
        artifact_type=None,
        output_file=None,
        output_dir=None,
        url=None,
    ):
        """Get list of artifact for a given file id."""
        artifacts = Artifacts(base_url=self.base_url, api_key=self.api_key)
        artifacts_content = artifacts.get_list(
            run_id=run_id, artifact_type=artifact_type
        )
        if not artifacts_content:
            raise Exception("Exception occurred.")

        if url:
            sys.stdout.write(artifacts_content["data"])
            sys.stdout.flush()
            return ("", "")
        if run_id and artifact_type:
            result = artifacts.save_artifacts(
                url=artifacts_content["data"],
                output_file=output_file,
                output_dir=output_dir,
            )

            if not result:
                raise Exception("Exception occurred during artifact creation.")
            LOGGER.info(f"Artifact has been saved to: {result}")
            LOGGER.info(f"Task Done")
            return ("", "")

        if run_id and artifact_type is None:
            artifacts_content = artifacts.get_artifacts(run_id=run_id)
            header = ["artifact_type"]
            if not artifacts_content:
                raise Exception("Exception occurred.")

            if not artifacts_content["artifacts"]:
                LOGGER.info(
                    f"\nThere are no artifacts for run id {artifacts_content['run_id']}"
                )
                return (header, [[" " for _ in range(len(header))]])

            body = [[i["artifact_type"]] for i in artifacts_content["artifacts"]]
            return (header, body)

    def report(self, file_id=None, output_file=None, output_dir=None):
        """Upload single file."""
        report = Reports(base_url=self.base_url, api_key=self.api_key, file_id=file_id)
        try:
            file_obj = Files(base_url=self.base_url, api_key=self.api_key)
            res = file_obj.get_file(file_id=file_id)
            if not res:
                raise CosmosidException(
                    f"Response from service is empty for file id {file_id}"
                )

            results = report.save_report(out_file=output_file, out_dir=output_dir)
            if results["status"]:
                return results
            else:
                raise CosmosidException(f'{results["message"]} File id: {file_id}')
        except CosmosidException as err:
            self.logger.error("Save report error")
            utils.log_traceback(err)

    def sample_run_list(self, file_id):
        """Get list of runs for a given file id."""
        sample_runs = Runs(base_url=self.base_url, api_key=self.api_key)
        try:
            sample_run_list = sample_runs.get_runs_list(file_id=file_id)
            if sample_run_list:
                if sample_run_list["status"]:
                    return sample_run_list
                else:
                    raise NotFoundException(sample_run_list["message"])
            else:
                raise CosmosidException(
                    f"Error occurred on get list of runs for a File: {file_id}"
                )
        except NotFoundException as err:
            self.logger.error("NotFound")
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error("Get runs list exception")
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error("Client exception occurred")
            utils.log_traceback(err)

    def pricing(self, data):
        """Get pricing information for the given list of samples and their sizes
        data:
        [  { "sample_key": "sample_name", "extension": "bam", "file_sizes": [100, 300]},
           ...
        ]

        """
        try:
            return upload.pricing(
                data=data, base_url=self.base_url, api_key=self.api_key
            )
        except Exception as err:
            self.logger.error(err)
            utils.log_traceback(err)

    def profile(self):
        """ "Get profile information for current user"""
        try:
            return auth.get_profile(self.base_url, {"X-Api-Key": self.api_key})
        except Exception as err:
            self.logger.error("Client exception occurred")
            utils.log_traceback(err)
            raise

    def download_samples(
        self, samples, concurrent_downloads, display_loading=True, output_dir=None
    ):
        try:
            original_samples = SamplesDownloader(
                base_url=self.base_url, api_key=self.api_key
            )

            file_paths = original_samples.download_samples(
                samples, output_dir, concurrent_downloads, display_loading
            )
            if file_paths:
                file_paths_text = "\n".join(file_paths)
                LOGGER.info(f"\nFiles were saved:\n{file_paths_text}\n\nTask Done")
            else:
                LOGGER.error(f"\nThere are not available files for downloading")
            return "", ""
        except Exception as err:
            raise DownloadSamplesException(f"{err}") from err
