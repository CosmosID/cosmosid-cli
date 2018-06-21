
import calendar
import logging
import os
import time
from datetime import datetime as dt
from operator import itemgetter

from cliff import _argparse
from cliff.command import Command
from cliff.lister import Lister

import cosmosid.utils as utils

LOGGER = logging.getLogger(__name__)


class ChoicesAction(_argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.choices.get(values, self.default))


class Files(Lister):
    """Show files in a given directory."""

    def get_parser(self, prog_name):
        parser = super(Files, self).get_parser(prog_name)
        parser.add_argument('--parent', '-p', type=str,
                            help='ID of the parent directory. Default: Root ')
        parser.add_argument('--order', '-o',
                            choices=['type', 'name', 'id', 'status', 'size',
                                     'created'], type=str,
                            help='field for ordering')
        parser.add_argument('--up', action='store_true', default=False,
                            help='order direction')
        return parser

    def take_action(self, parsed_args):
        """get json with items and prepare for output"""
        parent = utils.key_len(parsed_args.parent)
        folder_content = self.app.cosmosid.directory_list(parent)
        content_type_map = {
            '1': 'Folder',
            '2': 'Metagenomics Sample',
            '3': 'MRSA Sample',
            '4': 'Listeria Sample',
            '5': 'Amplicon 16S Sample',
            '6': 'Amplicon ITS Sample',
            '7': 'Microbiome Standard'
        }
        header = ['type', 'name', 'id', 'status', 'size', 'created']
        if folder_content:
            if not folder_content['items']:
                LOGGER.info('\nFolder %s (id: %s) is empty',
                            folder_content['name'], parent)
                for_output = [[' ', ' ', ' ', ' ', ' ', ' ']]
                return (header, for_output)
        else:
            raise Exception("Exception accured.")

        def _set_date(inp):
            try:
                utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return dt.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')

        def _del_none(inp):
            out = [inp[1]]
            if not out[0]:
                out = [0 if v[1] == 'int' else '-'
                       for _, v in field_maps.items() if inp[0] == v[0]]
            return out[0]

        def _set_dim(inp):
            out = inp if inp else 0
            out = utils.convert_size(out)
            return out if out != '0B' else '-'

        def _set_type(inp):
            ctype = (content_type_map[str(inp[1])]
                     if content_type_map.get(str(inp[1]))
                     else inp[1])
            return ctype

        def _convert(inp):
            for item in inp.items():
                for key, val in field_maps.items():
                    if item[0] == val[0]:
                        inp[item[0]] = field_maps[key][2](item)
                        break
            return inp

        field_maps = {
            'type': ['content_type', 'str', _set_type],
            'id': ['id', 'str', _del_none],
            'name': ['name', 'str', _del_none],
            'status': ['status', 'str', _del_none],
            'size': ['size', 'int', _del_none],
            'created': ['created', 'str', _set_date]
        }

        # we need just items for output
        items_data = [_convert(item) for item in folder_content['items']]

        # order regarding order parameters
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                items_data = sorted(
                    items_data,
                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                    reverse=(not parsed_args.up))
        for_output = [[item[field_maps[f][0]] if f != 'size'
                       else _set_dim(item[field_maps[f][0]])
                       for f in header]
                      for item in items_data]
        LOGGER.info('\nContent of the Folder %s (id: %s)',
                    folder_content['name'], parent)
        return (header, for_output)


class Upload(Command):
    """Upload files to cosmosid."""

    def get_parser(self, prog_name):
        parser = super(Upload, self).get_parser(prog_name)
        # grp = parser.add_mutually_exclusive_group(required=True)
        parser.add_argument(
            '--file', '-f',
            action='append',
            required=True,
            type=str,
            help='file(s) for upload. Supported file types: .fastq, .fasta, '
            '.fas, .fa, .seq, .fsa, .fq, .fna, .gz e.g. cosmosid upload -f '
            '/path/file1.fasta -f /path/file2.fn ')

        parser.add_argument('--parent', '-p',
                            action='store',
                            required=False,
                            type=str,
                            help='cosmosid parent folder ID for upload')

        choice = {'metagenomics': 2, 'amplicon-16s': 5, 'amplicon-its': 6}
        parser.add_argument('--type', '-t',
                            action=ChoicesAction,
                            required=True,
                            choices=choice,
                            type=str,
                            default=None,
                            help='Type of analysis for a file')

        return parser

    def take_action(self, parsed_args):
        """Send files to analysis."""
        parent_id = parsed_args.parent if parsed_args.parent else None
        parent_id = utils.key_len(parent_id, "ID")
        if parsed_args.file:
            for file in parsed_args.file:
                if not os.path.exists(file):
                    LOGGER.error('Specified file does not exist: %s', file)
                    continue
                LOGGER.info('File uploading is started: %s', file)
                file_id = self.app.cosmosid.upload_files(file,
                                                         parsed_args.type,
                                                         parent_id)
                if not file_id:
                    return False
                LOGGER.info('\nFile %s has been sent to analysis.', file)
                LOGGER.info('Use File ID to get Analysis Result: %s', file_id)
            LOGGER.info('Task Done')


class Analysis(Lister):
    """Show Analysis for a given file."""

    def get_parser(self, prog_name):
        parser = super(Analysis, self).get_parser(prog_name)
        grp = parser.add_mutually_exclusive_group(required=True)
        grp.add_argument('--id', '-i',
                         action='store',
                         type=str,
                         help='ID of a file')
        grp.add_argument('--run_id', '-r',
                         action='store',
                         type=str,
                         help='ID of a sample run')
        parser.add_argument('--order', '-o',
                            choices=['database', 'id', 'strains',
                                     'strains_filtered', 'status', 'created'],
                            type=str,
                            help='field for ordering')
        parser.add_argument('--up', action='store_true', default=False,
                            help='order direction')
        return parser

    def take_action(self, parsed_args):
        """get json with analysis for a file and prepare for output"""
        f_id = utils.key_len(parsed_args.id, "ID") if parsed_args.id else None
        r_id = (utils.key_len(parsed_args.run_id, "ID")
                if parsed_args.run_id
                else None)
        analysis_content = self.app.cosmosid.analysis_list(file_id=f_id,
                                                           run_id=r_id)

        header = ['id', 'database', 'strains', 'strains_filtered', 'status']
        if analysis_content:
            if not analysis_content['analysis']:
                LOGGER.info('\nThere are no analysis for run id %s',
                            analysis_content['run_id'])

                for_output = [[' ', ' ', ' ', ' ', ' ']]
                return (header, for_output)
        else:
            raise Exception("Exception uccured.")

        def _set_date(inp):
            try:
                utc_time_tuple = time.strptime(inp, "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(inp, "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return dt.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')

        def _del_none(inp):
            out = inp[1]
            if not out:
                out = 0 if field_maps[inp[0]][1] == 'int' else '-'
            return out

        def _convert(inp):
            database = inp['database']
            db_description = database['description']
            for item in inp.items():
                for k, v in field_maps.items():
                    if item[0] == v[0]:
                        inp[item[0]] = (field_maps[k][2](item)
                                        if item[0] != 'database'
                                        else db_description)
                        break
            return inp

        field_maps = {
            'id': ['id', 'str', _del_none],
            'database': ['database', 'str', _del_none],
            'status': ['status', 'str', _del_none],
            'strains': ['strains', 'int', _del_none],
            'strains_filtered': ['strains_filtered', 'int', _del_none]
        }

        run_metadata = analysis_content['run_meta']

        # we need just items for output
        items_data = [_convert(item) for item in analysis_content['analysis']]

        # order regarding order parameters
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                items_data = sorted(
                    items_data,
                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                    reverse=(not parsed_args.up))

        for_output = [[item[field_maps[field][0]] for field in header]
                      for item in items_data]

        if not r_id:
            LOGGER.info('Run ID is not entered. Analysis list from latest run '
                        '(%s) for file %s',
                        _set_date(run_metadata['created']),
                        run_metadata['file']['name'])

        LOGGER.info('\nAnalysis list for file %s and run id %s (%s)',
                    run_metadata['file']['name'], run_metadata['id'],
                    _set_date(run_metadata['created']))
        return (header, for_output)


class Reports(Command):
    """Get analysis reports CSV/PDF."""

    def get_parser(self, prog_name):
        parser = super(Reports, self).get_parser(prog_name)
        parser.add_argument('--id', '-i',
                            action='store',
                            required=True,
                            type=str,
                            help='ID of cosmosid file.')
        parser.add_argument('--run_id', '-r',
                            action='store',
                            required=False,
                            type=str,
                            help='ID of cosmosid sample run.')
        grp = parser.add_mutually_exclusive_group(required=False)
        grp.add_argument('--output', '-o',
                         action='store',
                         type=str,
                         help='output file name. Must have .zip extension. \
                               Default: is equivalent to cosmosid file name.')
        grp.add_argument('--dir', '-d',
                         action='store',
                         type=str,
                         help='output directory for a file. \
                               Default: is current directory.')
        return parser

    def take_action(self, parsed_args):
        """Save report to a given file."""
        f_id = utils.key_len(parsed_args.id, "ID") if parsed_args.id else None
        r_id = (utils.key_len(parsed_args.run_id, "ID")
                if parsed_args.run_id
                else None)
        output_file = parsed_args.output if parsed_args.output else None
        output_dir = parsed_args.dir if parsed_args.dir else None
        if not r_id:
            LOGGER.info('Processing reports for the latest run of file %s ...',
                        f_id)
        else:
            LOGGER.info('Processing reports for the run_id %s of file %s ...',
                        r_id, f_id)
        response = self.app.cosmosid.report(file_id=f_id,
                                            run_id=r_id,
                                            output_file=output_file,
                                            output_dir=output_dir)
        if response:
            LOGGER.info('\nReport has been saved to: %s',
                        response['saved_report'])
        else:
            raise Exception('Exception occured during report creation.')
        LOGGER.info('Task Done')


class Runs(Lister):
    """Show List Of Runs for a given File."""

    def get_parser(self, prog_name):
        parser = super(Runs, self).get_parser(prog_name)
        parser.add_argument('--id', '-i', type=str, required=True,
                            help='ID of the file')
        parser.add_argument('--order', '-o',
                            choices=['id', 'status', 'created'],
                            type=str,
                            help='field for ordering')
        parser.add_argument('--up', action='store_true', default=False,
                            help='order direction')
        return parser

    def take_action(self, parsed_args):
        """get json with runs for a file and prepare for output."""
        ids = utils.key_len(parsed_args.id, "ID")
        runs = self.app.cosmosid.sample_run_list(ids)
        header = ['id', 'status', 'created']
        if runs:
            if not runs['runs']:
                LOGGER.info('\nThere are no runs for file %s (id: %s)',
                            runs['file_name'], ids)

                for_output = [[' ', ' ', ' ']]
                return (header, for_output)
        else:
            raise Exception("Exception occured.")

        def _set_date(inp):
            try:
                utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return dt.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')

        def _del_none(inp):
            out = inp[1]
            if not out:
                out = 0 if field_maps[inp[0]][1] == 'int' else '-'
            return out

        def _convert(inp):
            for item in inp.items():
                for k, v in field_maps.items():
                    if item[0] == v[0]:
                        inp[item[0]] = field_maps[k][2](item)
                        break
            return inp

        field_maps = {
            'id': ['id', 'str', _del_none],
            'status': ['status', 'str', _del_none],
            'created': ['created', 'str', _set_date]}

        # we need just runs for output
        runs_data = [_convert(run) for run in runs['runs']]

        # order regarding order parameters
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                runs_data = sorted(
                    runs_data,
                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                    reverse=(not parsed_args.up))
        for_output = [[item[field_maps[field][0]] for field in header]
                      for item in runs_data]
        LOGGER.info('\nRuns list for file %s (id: %s)', runs['file_name'], ids)
        return (header, for_output)
