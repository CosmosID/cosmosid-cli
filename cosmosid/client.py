"""Python client."""

import logging

import cosmosid.api.upload as upload
import cosmosid.utils as utils
from cosmosid.api.analysis import Analysis
from cosmosid.api import auth
from cosmosid.api.files import Files, Runs
from cosmosid.api.reports import Reports
from cosmosid.helpers.auth import ApiKeyAuth
from cosmosid.helpers.exceptions import (CosmosidException, NotFoundException,
                                         UploadException, ValidationError)


class CosmosidApi(object):
    """
    Client is a python client on top of the CosmosID interface.
    """
    logger = logging.getLogger(__name__)

    BASE_URL = 'https://rest.cosmosid.com'

    def __init__(self, api_key=None, base_url=BASE_URL):
        """Initialize a client with the given params."""
        try:
            if not api_key:
                api_key = self.__auth()
            api_key = utils.key_len(api_key)
        except ValidationError as err:
            utils.log_traceback(err)
        base_url = base_url if base_url else self.BASE_URL
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

    def directory_list(self, parent):
        """"get listing of appropriate directory."""
        file_obj = Files(base_url=self.base_url, api_key=self.api_key)
        try:
            res = file_obj.get_list(parent_id=parent)
            if res:
                if res['status']:
                    return res
                else:
                    raise NotFoundException(res['message'])
            else:
                raise CosmosidException('Response from service is empty '
                                        'for directory {}'.format(parent))
        except NotFoundException as err:
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error('Get directory list exception')
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error("Failed to get listing of directory %s", parent)
            utils.log_traceback(err)

    def upload_files(self, files, file_type, parent_id=None):
        """Upload single file."""
        error_msg = '\nError occurred on File upload: {}'.format(files)
        try:
            upload_res = upload.upload_and_save(files=files,
                                                parent_id=parent_id,
                                                file_type=file_type,
                                                base_url=self.base_url,
                                                api_key=self.api_key)
            if upload_res:
                return upload_res['id']
            else:
                self.logger.error(error_msg)
        except UploadException as err:
            self.logger.error(error_msg)
            utils.log_traceback(err)

    def analysis_list(self, file_id=None, run_id=None):
        """Get list of analysis for a given file id."""
        analysis = Analysis(base_url=self.base_url, api_key=self.api_key)
        try:
            analysis_list = analysis.get_list(file_id=file_id, run_id=run_id)
            if analysis_list:
                if analysis_list['status']:
                    return analysis_list
                else:
                    raise NotFoundException(analysis_list['message'])
            else:
                raise CosmosidException('Error occurred on get list of '
                                        'analysis for a File: %s'
                                        % file_id)
        except NotFoundException as err:
            self.logger.error('NotFound')
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error('Get analysis list exception')
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error('Client exception occured')
            utils.log_traceback(err)

    def report(self, file_id=None, run_id=None, output_file=None,
               output_dir=None):
        """Upload single file."""
        report = Reports(base_url=self.base_url,
                         api_key=self.api_key,
                         file_id=file_id,
                         run_id=run_id)
        try:
            file_obj = Files(base_url=self.base_url, api_key=self.api_key)
            res = file_obj.get_file(file_id=file_id)
            if not res:
                raise CosmosidException('Response from service is empty '
                                        'for file id {}'.format(file_id))

            results = report.save_report(out_file=output_file,
                                         out_dir=output_dir)
            if results['status']:
                return results
            else:
                raise CosmosidException('{} File id: {}'.format(
                    results['message'],
                    file_id))
        except CosmosidException as err:
            self.logger.error('Save report error')
            utils.log_traceback(err)

    def sample_run_list(self, file_id):
        """Get list of runs for a given file id."""
        sample_runs = Runs(base_url=self.base_url, api_key=self.api_key)
        try:
            sample_run_list = sample_runs.get_runs_list(file_id=file_id)
            if sample_run_list:
                if sample_run_list['status']:
                    return sample_run_list
                else:
                    raise NotFoundException(sample_run_list['message'])
            else:
                raise CosmosidException('Error occurred on get list of runs '
                                        'for a File: %s' % file_id)
        except NotFoundException as err:
            self.logger.error('NotFound')
            utils.log_traceback(err)
        except CosmosidException as err:
            self.logger.error('Get runs list exception')
            utils.log_traceback(err)
        except Exception as err:
            self.logger.error('Client exception occured')
            utils.log_traceback(err)

    def pricing(self, data):
        """Get pricing information for the given list of samples and their sizes
            data:
            [  { "sample_key": "sample_name", "extension": "bam", "file_sizes": [100, 300]},
               ...
            ]

        """
        try:
            return upload.pricing(data=data, base_url=self.base_url, api_key=self.api_key)
        except Exception as err:
            self.logger.error(err)
            utils.log_traceback(err)

    def profile(self):
        """"Get profile information for current user"""
        try:
            return auth.get_profile(self.base_url, self.api_key)
        except Exception as err:
            self.logger.error('Client exception occured')
            utils.log_traceback(err)
            raise
