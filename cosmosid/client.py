"""Python client."""

import logging
import sys
from requests.exceptions import ConnectionError

import cosmosid.api.upload as upload
import cosmosid.utils as utils
from cosmosid.api import auth
from cosmosid.api.analysis import Analysis
from cosmosid.api.artifacts import Artifacts
from cosmosid.api.comparative_analyses import ComparativeAnalyses
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


class CosmosidApi:
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
        if not base_url.endswith("cosmosid.com"):
            raise CosmosidException("Base url is not valid!")
        base_url = base_url or self.BASE_URL
        if base_url != self.BASE_URL:
            self.logger.info("Using base URL: %s", base_url)
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'
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
            raise Exception("Can't get Cosmosid Api Key") from err
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
                    "Response from service is empty " "for directory {}".format(
                        parent)
                )
        except NotFoundException as err:
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error("Get directory list exception")
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error("Failed to get listing of directory %s", parent)
            utils.log_traceback(err)

    def make_dir(self, name, parent_id=None):
        file_obj = Files(base_url=self.base_url, api_key=self.api_key)
        new_folder_id = file_obj.make_dir(name=name, parent_id=parent_id)
        return new_folder_id    


    def get_enabled_workflows(self):
        workflow_api = Workflow(base_url=self.base_url, api_key=self.api_key)
        return workflow_api.get_workflows()

    def import_workflow(self, workflow_ids, pairs, file_type, parent_id=None, host_name=None, forward_primer=None, reverse_primer=None):
        import_wf = ImportWorkflow(base_url=self.base_url, api_key=self.api_key)
        try:
            for pair in pairs:
                for file in pair['files']:
                    pair.setdefault('files_s3', []).append(
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
                [{
                    "files": pair['files_s3'],
                    "file_name": pair["sample_name"]
                } for pair in pairs],
                file_type,
                parent_id,
                host_name,
                forward_primer,
                reverse_primer,
            )
        except NotFoundException as err:
            self.logger.error("Parent folder for upload doesn't exist.")
            raise err
        except UploadException as err:
            self.logger.error(
                "\nError occurred on File import: {}".format(pairs))
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
        if 'data' not in artifacts_content.keys():
            if artifacts_content.get('message'):
                raise Exception(artifacts_content['message'])
            raise Exception("No data.")

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
            self.logger.info(f"Artifact has been saved to: {result}")
            self.logger.info("Task Done")
            return ("", "")

        if run_id and artifact_type is None:
            artifacts_content = artifacts.get_artifacts(run_id=run_id)
            header = ["artifact_type"]
            if not artifacts_content:
                raise Exception("Exception occurred.")

            if not artifacts_content["artifacts"]:
                self.logger.info(
                    f"\nThere are no artifacts for run id {artifacts_content['run_id']}"
                )
                return (header, [[" " for _ in range(len(header))]])
            self.logger.info(f"Artifacts list for run id: {run_id}")
            body = [[i["artifact_type"]]
                    for i in artifacts_content["artifacts"]]
            return (header, body)

    def report(self, file_id=None, output_file=None, output_dir=None, timeout=300):
        """Upload single file."""
        report = Reports(base_url=self.base_url,
                         api_key=self.api_key, file_id=file_id, timeout=timeout)
        try:
            file_obj = Files(base_url=self.base_url, api_key=self.api_key)
            res = file_obj.get_file(file_id=file_id)
            if not res:
                raise CosmosidException(
                    f"Response from service is empty for file id {file_id}"
                )

            results = report.save_report(
                out_file=output_file, out_dir=output_dir)
            if results["status"]:
                return results
            else:
                raise CosmosidException(
                    f'{results["message"]} File id: {file_id}')
        except CosmosidException as err:
            self.logger.error("Save report error")
            utils.log_traceback(err)

    def sample_run_list(self, file_id):
        """Get list of runs for a given file id."""
        sample_runs = Runs(base_url=self.base_url, api_key=self.api_key)
        return sample_runs.get_runs_list(file_id=file_id)

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
                self.logger.info(
                    f"\nFiles were saved:\n{file_paths_text}\n\nTask Done")
            else:
                self.logger.error(
                    "\nThere are not available files for downloading")
            return "", ""
        except Exception as err:
            raise DownloadSamplesException(f"{err}") from err

    def get_analyses(self, comparative_ids):
        if comparative_ids:
            return ComparativeAnalyses(
                self.base_url, self.api_key
            ).get_analyses_of_comparative(self.profile()['id'], comparative_ids)
        return ComparativeAnalyses(self.base_url, self.api_key).get_analyses_out_of_comparatives()

    def get_comparatives(self):
        return ComparativeAnalyses(self.base_url, self.api_key).get_comparatives(self.profile()['id'])

    def export_analyses(self,
                        analyses_ids,
                        export_types,
                        concurrent_downloads,
                        output_dir,
                        log_scale,
                        tax_levels
                        ):
        return ComparativeAnalyses(self.base_url, self.api_key).export_analyses(
            analyses_ids,
            export_types,
            concurrent_downloads,
            output_dir,
            log_scale,
            tax_levels
        )
