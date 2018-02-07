
import os
import logging
import calendar
import time
import cosmosid.utils as utils

from operator import itemgetter
from datetime import datetime as dt
from cliff.command import Command
from cliff.lister import Lister
from cliff import _argparse


class ChoicesAction(_argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.choices.get(values, self.default))


class Files(Lister):
    """Show files in a given directory."""
    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Files, self).get_parser(prog_name)
        parser.add_argument('--parent', '-p', type=str, help='ID of the parent directory. Default: Root ')
        parser.add_argument('--order', '-o',
                            choices=['type', 'name', 'id', 'status', 'size', 'created'],
                            type=str,
                            help='field for ordering')
        parser.add_argument('--up', action='store_true', default=False, help='order direction')
        return parser

    def take_action(self, parsed_args):
        """get json with items and prepare for output"""
        folder_content = dict()
        parent = utils.key_len(parsed_args.parent)
        folder_content = self.app.cosmosid.directory_list(parent)
        content_type_map = {
            '1': 'Folder',
            '2': 'Metagenomics Sample',
            '3': 'MRSA Sample',
            '4': 'Listeria Sample',
            '5': 'Amplicon 16S Sample',
            '6': 'Amplicon ITS Sample'
        }
        header = ['type', 'name', 'id', 'status', 'size', 'created']
        if folder_content:
            if not folder_content['items']:
                self.logger.info('\nFolder {} (id: {}) is empty'.format(folder_content['name'], parent))
                for_output = [[' ', ' ', ' ', ' ', ' ', ' ']]
                return (header, for_output)
        else:
            raise Exception("Exception uccured.")

        def _set_date(inp):
            utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S.%f")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return dt.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')

        def _del_none(inp):
            out = [inp[1]]
            if not out[0]:
                out = [0 if v[1] == 'int' else '-' for k, v in field_maps.items() if inp[0] == v[0]]
            return out[0]

        def _set_dim(inp):
            out = inp if inp else 0
            out = utils.convert_size(out)
            return out if out is not '0B' else '-'

        def _set_type(inp):
            ctype = content_type_map[str(inp[1])] if content_type_map.get(str(inp[1])) else inp[1]
            return ctype

        def _convert(inp):
            for item in inp.items():
                for k, v in field_maps.items():
                    if item[0] == v[0]:
                        inp[item[0]] = field_maps[k][2](item)
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

        """we need just items for output"""
        items_data = [_convert(item) for item in folder_content['items']]

        """order regarding order parameters"""
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                items_data = sorted(items_data,
                                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                                    reverse=(not parsed_args.up)
                                    )
        for_output = [[item[field_maps[f][0]] if f is not 'size'
                       else _set_dim(item[field_maps[f][0]])
                       for f in header]
                      for item in items_data
                      ]
        self.logger.info('\nContent of the Folder {} (id: {})'.format(folder_content['name'], parent))
        return (header, for_output)


class Upload(Command):
    """Upload files to cosmosid."""

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Upload, self).get_parser(prog_name)
        # grp = parser.add_mutually_exclusive_group(required=True)
        parser.add_argument('--file', '-f',
                            action='append',
                            required=True,
                            type=str,
                            help='file(s) for upload \
                                  Supported file types: .fastq, .fasta, .fas, .fa, .seq, .fsa, .fq, .fna, .gz \
                                  e.g. cosmosid upload -f /path/file1.fasta -f /path/file2.fn \
                                  '
                            )
        parser.add_argument('--parent', '-p',
                            action='store',
                            required=False,
                            type=str,
                            help='cosmosid parent folder ID for upload'
                            )

        # choice = {'metagenomics': 2, 'amplicon': 5, 'mrsa': 3, 'listeria': 4}
        choice = {'metagenomics': 2, 'amplicon-16s': 5, 'amplicon-its': 6}
        parser.add_argument('--type', '-t',
                            action=ChoicesAction,
                            required=True,
                            choices=choice,
                            type=str,
                            default=None,
                            help='Type of analysis for a file'
                            )

        # grp.add_argument('--dir', '-d',
        #                 type=str,
        #                 action='store',
        #                 help='directory with files for upload from, e.g. cosmosid upload -d /path/dir_with_samples')

        return parser

    def take_action(self, parsed_args):
        """Send files to analysis."""
        parent_id = parsed_args.parent if parsed_args.parent else None
        parent_id = utils.key_len(parent_id, "ID")
        if parsed_args.file:
            for file in parsed_args.file:
                if not os.path.exists(file):
                    self.logger.error('Specified file does not exist: {}'.format(file))
                    continue
                self.logger.info('File uploading is started: {}'.format(file))
                file_id = self.app.cosmosid.upload_files(file, parsed_args.type, parent_id)
                if not file_id:
                    return False
                self.logger.info('File {} has been sent to analysis.'.format(file))
                self.logger.info('Use File ID to get Analysis Result: {}'.format(file_id))
            self.logger.info('Task Done')


class Analysis(Lister):
    """Show Analysis for a given file."""

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Analysis, self).get_parser(prog_name)
        parser.add_argument('--id', '-i', type=str, required=True, help='ID of the file')
        parser.add_argument('--order', '-o',
                            choices=['database', 'id', 'strains', 'strains_filtered', 'status', 'created'],
                            type=str,
                            help='field for ordering')
        parser.add_argument('--up', action='store_true', default=False, help='order direction')
        return parser

    def take_action(self, parsed_args):
        """get json with analysis for a file and prepare for output"""
        analysis_content = dict()
        ids = utils.key_len(parsed_args.id, "ID")
        analysis_content = self.app.cosmosid.analysis_list(ids)
        header = ['id', 'database', 'database_version', 'strains', 'strains_filtered', 'status']
        if analysis_content:
            if not analysis_content['items']:
                self.logger.info('\nThere are no analysis for file {} (id: {})'.
                                 format(analysis_content['file_metadata']['name'], ids)
                                 )
                for_output = [[' ', ' ', ' ', ' ', ' ', ' ']]
                return (header, for_output)
        else:
            raise Exception("Exception uccured.")

        def _set_date(inp):
            utc_time_tuple = time.strptime(inp, "%Y-%m-%dT%H:%M:%S.%f")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return dt.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')

        def _del_none(inp):
            out = inp[1]
            if not out:
                out = 0 if field_maps[inp[0]][1] == 'int' else '-'
            return out

        def _convert(inp):
            version = inp['database_version']
            # date_run = inp['created'] if inp['created'] else analysis_content['file_metadata']['created']
            # date_run = _set_date(date_run)
            db_version = "{}".format(version)
            for item in inp.items():
                for k, v in field_maps.items():
                    if item[0] == v[0]:
                        inp[item[0]] = field_maps[k][2](item) if item[0] != 'database_version' else db_version
                        break
            return inp

        field_maps = {
            'id': ['id', 'str', _del_none],
            'database': ['description', 'str', _del_none],
            'database_version': ['database_version', 'str', _del_none],
            'status': ['status', 'str', _del_none],
            'strains': ['strains', 'int', _del_none],
            'strains_filtered': ['strains_filtered', 'int', _del_none]
        }

        """we need just items for output"""
        items_data = [_convert(item) for item in analysis_content['items']]

        """order regarding order parameters"""
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                items_data = sorted(items_data,
                                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                                    reverse=(not parsed_args.up)
                                    )
        create_date = _set_date(analysis_content['file_metadata']['created'])
        for_output = [[item[field_maps[field][0]] for field in header] for item in items_data]
        self.logger.info('\nAnalysis list for {} (id: {}). Creation date: {}'
                         .format(analysis_content['file_metadata']['name'], ids, create_date))
        return (header, for_output)


class Reports(Command):
    """Get analysis reports CSV/PDF."""

    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Reports, self).get_parser(prog_name)
        parser.add_argument('--id', '-i',
                            action='store',
                            required=True,
                            type=str,
                            help='ID of cosmosid file.'
                            )
        grp = parser.add_mutually_exclusive_group(required=False)
        grp.add_argument('--output', '-o',
                         action='store',
                         type=str,
                         help='output file name. Must have .zip extension. \
                               Default: is equivalent to cosmosid file name.'
                         )
        grp.add_argument('--dir', '-d',
                         action='store',
                         type=str,
                         help='output directory for a file. \
                               Default: is current directory.'
                         )
        return parser

    def take_action(self, parsed_args):
        """Save report to a given file."""
        ids = utils.key_len(parsed_args.id, "ID")
        output_file = parsed_args.output if parsed_args.output else None
        output_dir = parsed_args.dir if parsed_args.dir else None
        self.logger.info('Processing reports for file {} ...'.format(ids))
        response = self.app.cosmosid.report(ids, output_file=output_file, output_dir=output_dir)
        if response:
            self.logger.info('\nReport has been saved to: {}'.format(response))
        else:
            raise Exception('Exception occured during report creation.')
        self.logger.info('Task Done')
