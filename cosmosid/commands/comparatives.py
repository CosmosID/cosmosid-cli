from cliff.lister import Lister
from cosmosid import utils
from cosmosid.helpers.exceptions import NotFoundException


class Comparatives(Lister):
    """List of comparatives"""

    def take_action(self, parsed_args):
        comparatives = self.app.cosmosid.get_comparatives()
        if not comparatives:
            raise NotFoundException('No comparatives were found')

        data = utils.get_table_from_json(comparatives)
        for name, label in (
            ('uuid', 'ID'),
            ('name', 'Name'),
            ('created', 'Created'),
            ('status', 'Status')
        ):
            if name in data[0]:
                data[0][data[0].index(name)] = label

        return data

    def produce_output(self, parsed_args, column_names, data):
        if not parsed_args.columns:
            parsed_args.columns = ['ID', 'Name', 'Created', 'Status']
        elif '*' in parsed_args.columns:
            parsed_args.columns = list(column_names)
        return super(Comparatives, self).produce_output(parsed_args, column_names, data)
