import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress

import requests
from cosmosid.config import CHUNK_SIZE, CONCURRENT_DOWNLOADS
from cosmosid.helpers.downloader import Downloader
from cosmosid.utils import retry, get_valid_name
from cosmosid.enums import ComparativeExportType

logger = logging.getLogger(__name__)


class ComparativeAnalyses:

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        api_url = f'{base_url}/api/metagenid/v1/comparative'
        comparative_api_url = f'{base_url}/api/comparative/v1/users/{{user_id}}/comparatives'
        export_by_analysis_id_api_url = f'{api_url}/{{analysis_id}}/tsv'
        self._urls = {
            'list-of-analysis': f'{api_url}?offset={{offset}}&order_by=-created_at&limit={{limit}}',
            'list-of-comparatives': comparative_api_url,
            'comparative-info': f'{comparative_api_url}/{{comparative_id}}',
            'analysis-info': f'{api_url}/{{analysis_id}}',
            'multiqc-zip-info': f'{api_url}/{{analysis_id}}',
            'multiqc-zip-run-id': f'{api_url}/{{analysis_id}}/results/multiqc',
            ComparativeExportType.matrix.value: f'{export_by_analysis_id_api_url}/matrix?tax_level={{tax_level}}&log_scale={{log_scale}}',
            ComparativeExportType.alpha_diversity.value: f'{export_by_analysis_id_api_url}/alphazip',
            ComparativeExportType.beta_diversity.value: f'{export_by_analysis_id_api_url}/betazip',
            ComparativeExportType.read_statistics.value: f'{export_by_analysis_id_api_url}/read-statistics',
            ComparativeExportType.multiqc.value: f'{base_url}/api/metagenid/v1/runs/{{run_id}}/artifacts/multiqc-zip',
            ComparativeExportType.ampliseq_summary.value: f'{export_by_analysis_id_api_url}/ampliseq-summary',
            ComparativeExportType.lefse.value: f'{export_by_analysis_id_api_url}/lefse',
        }

        self._default__available_types = (
            ComparativeExportType.matrix.value, ComparativeExportType.alpha_diversity.value,
            ComparativeExportType.beta_diversity.value, ComparativeExportType.read_statistics.value,
            ComparativeExportType.ampliseq_summary.value, ComparativeExportType.lefse.value
        )
        self._available_types = {
            'multiqc': (ComparativeExportType.multiqc.value,)
        }

    def _validate(self, analysis_type, export_type):
        available_export_types = self._available_types.get(
            analysis_type, self._default__available_types)
        if export_type not in available_export_types:
            return False
        return True

    def _get_data(self, url_key, **kwargs):
        resp = requests.get(
            self._urls[url_key].format(**kwargs),
            headers={
                'X-Api-key': self.api_key
            })
        resp.raise_for_status()
        return resp.json()

    @retry(requests.Timeout, tries=3, delay=2, raise_error=True)
    def get_analyses_out_of_comparatives(self):
        step = 500
        data = self._get_data('list-of-analysis', offset=0, limit=1)
        records_amount = data['total_amount']
        result = []
        for offset in range(0, records_amount + 1, step):
            result.extend([{
                'ID': analysis['id'],
                'Name': analysis['name'],
                'Database ID': analysis['database_id'],
                'Database name': analysis['database_name'],
                'Log': analysis['log'],
                'Metric': analysis['field'],
                'Created': analysis['created_at'],
                'Filterset': analysis['filterset'],
                'Status': analysis['status'],
                'Status description': analysis['status_description']
            } for analysis in self._get_data('list-of-analysis', offset=offset, limit=step)['analysis']])
        return result

    @retry(requests.Timeout, tries=3, delay=2, raise_error=True)
    def get_analyses_of_comparative(self, user_id, comparative_ids):
        def get_comparative(_comparative, _process):
            try:
                analysis = self._get_data(
                    'analysis-info', analysis_id=_process['child_ca_uuid'])
            except requests.RequestException:
                return
            return {
                'Name': _comparative['name'],
                'Comparative ID': _comparative['id'],
                'ID': _process['child_ca_uuid'],
                'Process': _process['workflow_process_uuid'],
                # 'Process status': _process['workflow_process_status'],
                'Database ID': analysis['database_id'],
                'Database name': analysis['database_name'],
                'Log': analysis['log'],
                'Metric': analysis['field'],
                'Created': analysis['created_at'],
                'Filterset': analysis['filterset'],
                'Status': analysis['status'],
                'Status description': analysis['status_description'],
            }

        tasks = []
        for comparative_id in comparative_ids:
            with suppress(requests.RequestException):
                comparative = self._get_data(
                    'comparative-info', user_id=user_id, comparative_id=comparative_id)
                comparative['id'] = comparative_id
                for process in comparative['processes']:
                    tasks.append(
                        (comparative, process)
                    )

        analyses = []
        with ThreadPoolExecutor(
                max_workers=CONCURRENT_DOWNLOADS * 2
        ) as executor:
            future_to_task = {
                executor.submit(
                    get_comparative, *task
                ): task
                for task in tasks
            }
            for future in as_completed(future_to_task):
                analysis = future.result()
                if analysis:
                    analyses.append(analysis)
        return analyses

    @retry(requests.Timeout, tries=3, delay=2, raise_error=True)
    def get_comparatives(self, user_id):
        return self._get_data('list-of-comparatives', user_id=user_id)['analysis']

    def _get_download_link(self, analysis_id, export_type, **kwargs):
        if export_type == ComparativeExportType.multiqc.value:
            kwargs['run_id'] = self._get_data(
                'multiqc-zip-run-id',
                analysis_id=analysis_id
            )['result']['process_id']
        data = self._get_data(export_type, analysis_id=analysis_id, **kwargs)
        return data['data'] if export_type == ComparativeExportType.multiqc.value else data['url']

    def export_analysis(
            self,
            url,
            filename,
            directory,
    ):
        path = os.path.join(directory, filename)
        try:
            Downloader.load_file(
                url,
                None,
                filename,
                directory,
                CHUNK_SIZE,
            )
            return path
        except FileExistsError:
            logger.error(f'File {path} already exists!')
        except Exception as error:
            logger.error(path + ': ' + error)

    def _get_all_options(self, export_types, tax_levels, analyses_ids, log_scale, output_dir):

        def get_option(analysis_id, export_type, **kwargs):
            if not self._validate(analyses[analysis_id]['database_name'].lower(), export_type):
                return
            try:
                download_link = self._get_download_link(
                    analysis_id, export_type=export_type, **kwargs)
            except requests.exceptions.RequestException:
                return
            ext = download_link.split("/")[6].split("?")[0].split('.')[-1]
            option = {
                'analysis': analyses[analysis_id],
                'directory': directories[analysis_id],
                'export_type': export_type,
                'url': download_link
            }
            if export_type == ComparativeExportType.matrix.value:
                option.update({
                    'tax_level': kwargs['tax_level'],
                    'log_scale': kwargs['log_scale'],
                    'filename': f'matrix_{tax_level}' + (
                        '_with_log_scale.' if kwargs['log_scale'] == 'true' else '.'
                    ) + ext
                })
            else:
                option['filename'] = f'{export_type}.{ext}'
            return option
        res = []
        analyses = {}
        for analysis_id in analyses_ids.copy():
            try:
                analyses[analysis_id] = self._get_data(
                    'analysis-info', analysis_id=analysis_id)
            except requests.HTTPError:
                analyses_ids.remove(analysis_id)
        directories = {
            analysis_id: os.path.join(
                output_dir, get_valid_name(analyses[analysis_id]['name']))
            for analysis_id in analyses_ids
        }

        if ComparativeExportType.matrix.value in export_types:
            for analysis_id in analyses_ids:
                for tax_level in tax_levels:
                    option = get_option(
                        analysis_id, ComparativeExportType.matrix.value,
                        tax_level=tax_level,
                        log_scale='false'
                    )
                    if option is not None:
                        res.append(option)
                    if log_scale:
                        option = get_option(
                            analysis_id, ComparativeExportType.matrix.value,
                            tax_level=tax_level,
                            log_scale='true'
                        )
                        if option is not None:
                            res.append(option)
        for analysis_id in analyses_ids:
            for export_type in export_types:
                if export_type == ComparativeExportType.matrix.value:
                    continue
                option = get_option(analysis_id, export_type)
                if option is not None:
                    res.append(option)
        return res

    @retry(requests.Timeout, tries=3, delay=2, raise_error=True)
    def export_analyses(
            self,
            analyses_ids,
            export_types,
            concurrent_downloads,
            output_dir,
            log_scale,
            tax_levels
    ):

        logger.info("Looking for available comparative analyses...")

        all_options = self._get_all_options(
            export_types, tax_levels, analyses_ids, log_scale, output_dir)

        if not all_options:
            logger.error('No available comparative analyses were found!')
            return

        logger.info('The files to download:\n' + '\n'.join([
            os.path.join(option['directory'], option['filename']) for option in all_options
        ]))

        for directory in set(map(lambda option: option['directory'], all_options)):
            if not os.path.exists(directory) or not os.path.isdir(directory):
                os.mkdir(directory)

        logger.info('\nLoading...')
        success = False
        with ThreadPoolExecutor(
                max_workers=concurrent_downloads or CONCURRENT_DOWNLOADS
        ) as executor:
            future_to_url = {
                executor.submit(
                    self.export_analysis,
                    directory=option['directory'],
                    filename=option['filename'],
                    url=option['url'],
                ): option['analysis']['id']
                for option in all_options
            }
            for future in as_completed(future_to_url):
                if future.done():
                    error = future.exception(1)
                    if error is None:
                        filepath = future.result()
                        if filepath:
                            success = True
                            logger.info(
                                f'The file: {filepath} downloaded')
                    else:
                        logger.error(error)
        if success:
            logger.info('Completed')
        else:
            logger.error('\nThe operation has failed')
