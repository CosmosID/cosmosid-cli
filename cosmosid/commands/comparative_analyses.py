from cliff.lister import Lister
from cosmosid.helpers import argument_validators
from cosmosid import utils


class ComparativeAnalyses(Lister):
    """List of all comparative analyses outside comparatives (if there are no any comparative ids)"""
    def get_parser(self, prog_name):
        parser = super(ComparativeAnalyses, self).get_parser(prog_name)
        parser.add_argument(
            '--comparative-id',
            action='append',
            type=argument_validators.uuid,
            help='Comparatives\' ids'
        )
        return parser

    def take_action(self, parsed_args):
        analyses = self.app.cosmosid.get_analyses(parsed_args.comparative_id)
        if not analyses:
            raise ValueError('No analyses were found')
        return utils.get_table_from_json(analyses)

    def produce_output(self, parsed_args, column_names, data):
        if not parsed_args.columns:
            parsed_args.columns = ['ID', 'Name', 'Database name',
                                   'Created', 'Status']
        elif '*' in parsed_args.columns:
            parsed_args.columns = list(column_names)
        return super(ComparativeAnalyses, self).produce_output(parsed_args, column_names, data)
