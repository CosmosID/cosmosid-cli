from cliff.command import Command
from cosmosid.helpers import argument_validators
from cosmosid.helpers import parser_builders
from cosmosid.enums import ComparativeExportType, TaxonomicRank

import logging

logger = logging.getLogger(__name__)


class ComparativeAnalysesExport(Command):
    """Download results of comparative analyses"""

    def get_parser(self, prog_name):
        parser = super(ComparativeAnalysesExport, self).get_parser(prog_name)
        parser.add_argument(
            '--id',
            action='append',
            required=True,
            type=argument_validators.uuid,
            help='IDs of comparative analyses',
        )
        parser.add_argument(
            '--tax-level',
            action='append',
            default=[],
            choices=[tax_rank.value for tax_rank in TaxonomicRank],
            help='Taxonomy'
        )
        parser.add_argument(
            '--log-scale',
            default=False,
            action='store_true',
            help='Includes results with logscale'
        )

        parser.add_argument(
            "--concurrent-downloads",
            action="store",
            type=int,
            default=None,
            help="Limit concurrent files downloads",
        )
        parser_builders.directory(parser)
        return parser

    def take_action(self, parsed_args):
        kwargs = {
            key: getattr(parsed_args, key)
            for key in set(vars(parsed_args).keys()) & {'log_scale', 'tax_level'}
        }
        if 'log_scale' in kwargs.keys():
            kwargs['log_scale'] = str(kwargs['log_scale']).lower()
        comparaitive_ids = list(set(parsed_args.id))
        if len(comparaitive_ids) != len(parsed_args.id):
            logger.warning('Duplicated comparative ids!')
        self.app.cosmosid.export_analyses(
            comparaitive_ids,
            [export_type.value for export_type in ComparativeExportType],
            parsed_args.concurrent_downloads,
            parsed_args.dir,
            parsed_args.log_scale,
            parsed_args.tax_level or [TaxonomicRank.species.value, ],
        )
