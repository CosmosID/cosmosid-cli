import sys
import logging

from cosmosid.helpers.auth import ApiKeyAuth
from cosmosid.helpers.exceptions import ValidationError, CosmosidException, UploadException, NotFoundException
import cosmosid.utils as utils
from cosmosid.api.files import Files
import cosmosid.api.upload as upload
from cosmosid.api.analysis import Analysis
from cosmosid.api.reports import Reports


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
        except ValidationError as ve:
            self.logger.error("Api Key Validation Error: {}".format(ve))
            sys.exit(1)
        base_url = base_url if base_url else self.BASE_URL
        if base_url != self.BASE_URL:
            self.logger.warn("Using base URL: {}".format(base_url))
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
        except (KeyError, ValueError):
            self.logger.error("Cann't get Cosmosid Api Key")
            sys.exit(1)
        return api_key

    def directory_list(self, parent):
        """"get listing of appropriate directory."""
        fo = Files(base_url=self.base_url, api_key=self.api_key)
        try:
            res = fo.get_list(parent_id=parent)
            if res:
                if res['status']:
                    return res
                else:
                    raise NotFoundException(res['message'])
            else:
                raise CosmosidException('Response from service is empty for directory {}'.format(parent))
        except NotFoundException as nfex:
            self.logger.error('NotFound: {}'.format(nfex))
        except CosmosidException as mex:
            self.logger.error('Get directory list exception: {}'.format(mex))
        except Exception:
            self.logger.error("failed to get listing of directory {}".format(parent))

    def upload_files(self, file, file_type, parent_id=None):
        """Upload single file."""
        try:
            upload_res = upload.upload_file(file=file,
                                            parent_id=parent_id,
                                            file_type=file_type,
                                            base_url=self.base_url,
                                            api_key=self.api_key
                                            )
            if upload_res:
                return upload_res['created'][0]
            else:
                raise UploadException('Error uccurred on File upload: {}'.format(file))
        except UploadException as uex:
            self.logger.error('File upload error: {}'.format(uex))

    def analysis_list(self, file):
        """Get list of analysis for a given file id."""
        analysis = Analysis(base_url=self.base_url, api_key=self.api_key)
        try:
            analysis_list = analysis.get_list(file_id=file)
            if analysis_list:
                if analysis_list['status']:
                    return analysis_list
                else:
                    raise NotFoundException(analysis_list['message'])
            else:
                raise CosmosidException('Error uccurred on get list of analysis for a File: {}'.format(file))
        except NotFoundException as nfex:
            self.logger.error('NotFound: {}'.format(nfex))
        except CosmosidException as mex:
            self.logger.error('Get analysis list exception: {}'.format(mex))
        except Exception as ex:
            self.logger.error('Client exception occured: {}'.format(ex))

    def report(self, file_id, output_file=None, output_dir=None):
        """Upload single file."""
        report = Reports(base_url=self.base_url,
                         api_key=self.api_key,
                         file_id=file_id
                         )
        try:
            results = report.save_report(out_file=output_file, out_dir=output_dir)
            if results['status']:
                return results['saved_report']
            else:
                raise CosmosidException('{} File id: {}'.format(results['message'], file_id))
        except CosmosidException as mex:
            self.logger.error('Save report error: {}'.format(mex))
