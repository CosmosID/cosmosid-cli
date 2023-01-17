import time
import calendar

from cliff.lister import Lister
from cosmosid import utils
from datetime import datetime
from operator import itemgetter


class Files(Lister):
    """Show files in a given directory."""

    def get_parser(self, prog_name):
        parser = super(Files, self).get_parser(prog_name)
        parser.add_argument(
            "--parent",
            "-p",
            type=str,
            help="ID of the parent directory. Default: Root ",
        )
        parser.add_argument(
            "--order",
            "-o",
            choices=["type", "name", "id", "status", "reads", "created"],
            type=str,
            help="field for ordering",
        )
        parser.add_argument(
            "--up", action="store_true", default=False, help="order direction"
        )
        return parser

    def take_action(self, parsed_args):
        """get json with items and prepare for output"""
        parent = utils.key_len(parsed_args.parent)
        folder_content = self.app.cosmosid.dashboard(parent)
        content_type_map = {
            "1": "Folder",
            "2": "Metagenomics Sample",
            "3": "MRSA Sample",
            "4": "Listeria Sample",
            "5": "Amplicon 16S Sample",
            "6": "Amplicon ITS Sample",
        }
        header = ["type", "name", "id", "status", "reads", "created"]
        if folder_content:
            if not folder_content["items"]:
                self.app.logger.info(f"\nFolder {parent} is empty")
                for_output = [[" ", " ", " ", " ", " ", " "]]
                return (header, for_output)
        else:
            raise Exception("Exception accured.")

        def _set_date(input_date):
            try:
                utc_time_tuple = time.strptime(
                    input_date[1], "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(
                    input_date[1], "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            return datetime.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")

        def _del_none(inp):
            out = [inp[1]]
            if not out[0]:
                out = [
                    0 if v[1] == "int" else "-"
                    for _, v in field_maps.items()
                    if inp[0] == v[0]
                ]
            return out[0]

        def _set_dim(inp):
            out = inp if inp else 0
            out = utils.convert_size(out)
            return out if out != "0B" else "-"

        def _set_type(inp):
            ctype = (
                content_type_map[str(inp[1])]
                if content_type_map.get(str(inp[1]))
                else inp[1]
            )
            return ctype

        def _convert(inp):
            for item in inp.items():
                for key, val in field_maps.items():
                    if item[0] == val[0]:
                        inp[item[0]] = field_maps[key][2](item)
                        break
            return inp

        field_maps = {
            "type": ["type", "str", _set_type],
            "id": ["id", "str", _del_none],
            "name": ["name", "str", _del_none],
            "status": ["status", "str", _del_none],
            "reads": ["reads", "int", _del_none],
            "created": ["created", "str", _set_date],
        }

        items_data = [_convert(item) for item in folder_content["items"]]

        # order regarding order parameters
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                items_data = sorted(
                    items_data,
                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                    reverse=(not parsed_args.up),
                )
        for_output = [
            [
                item[field_maps[f][0]]
                if f != "reads"
                else _set_dim(item[field_maps[f][0]])
                for f in header
            ]
            for item in items_data
        ]
        self.app.logger.info(f"\nContent of the Folder {parent}")
        return (header, for_output)
