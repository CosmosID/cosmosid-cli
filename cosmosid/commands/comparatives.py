from cliff.lister import Lister
from cosmosid import utils


class Comparatives(Lister):
    """List of comparatives"""

    def take_action(self, parsed_args):
        data = utils.get_table_from_json(self.app.cosmosid.get_comparatives())

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
