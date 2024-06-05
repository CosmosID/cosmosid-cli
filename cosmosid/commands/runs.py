import time
import calendar
from datetime import datetime
from operator import itemgetter

from cosmosid import utils
from cliff.lister import Lister
from cosmosid.helpers import argument_validators


class Runs(Lister):
    """Show List Of Runs for a given File."""

    def get_parser(self, prog_name):
        parser = super(Runs, self).get_parser(prog_name)
        parser.add_argument(
            "--id", "-i", type=argument_validators.uuid, required=True, help="ID of the sample"
        )
        parser.add_argument(
            "--order",
            "-o",
            choices=["id", "status", "created"],
            type=str,
            help="field for ordering",
            required=False,
        )
        parser.add_argument(
            "--up",
            action="store_true",
            default=False,
            help="order direction",
            required=False,
        )
        return parser

    def take_action(self, parsed_args):
        """get json with runs for a file and prepare for output."""
        ids = utils.key_len(parsed_args.id, "ID")
        runs = self.app.cosmosid.sample_run_list(ids)
        header = [
            "id",
            "created",
            "workflow_name",
            "workflow_version",
            "status",
            "artifact_types",
        ]
        for_output = [["" for _ in header]]
        if runs:
            if not runs["runs"]:
                self.app.logger.info(
                    "\nThere are no runs for sample %s (id: %s)", runs["file_name"], ids
                )

                for_output = [["" for i in header]]
                return (header, for_output)
        else:
            raise Exception("Exception occurred.")

        def _set_date(inp):
            try:
                utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(inp[1], "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return datetime.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")

        def _del_none(inp):
            return inp[1] or (0 if field_maps[inp[0]][1] == "int" else "-")

        def _convert(inp):
            for item in inp.items():
                for k, v in field_maps.items():
                    if item[0] == v[0]:
                        inp[item[0]] = field_maps[k][2](item)
                        break
            return inp

        field_maps = {
            "id": ["id", "str", _del_none],
            "status": ["status", "str", _del_none],
            "created": ["created", "str", _set_date],
            "workflow_id": ["workflow_id", "str", _del_none],
            "workflow_name": ["workflow_name", "str", _del_none],
            "workflow_version": ["workflow_version", "str", _del_none],
            "artifact_types": ["artifact_types", "str", _del_none],
        }

        # we need just runs for output
        runs_data = [_convert(run) for run in runs["runs"]]

        # order regarding order parameters
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                runs_data = sorted(
                    runs_data,
                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                    reverse=(not parsed_args.up),
                )
        for_output = []
        for item in runs_data:

            items = []
            for field in header:
                name = field_maps[field][0]
                i = item[name]
                if name == "artifact_types":
                    artifacts = i.split(",")
                    i = "".join([f"{a} \n" for a in artifacts])

                items.append(i)

            for_output.append(items)

        self.app.logger.info(
            "\nRuns list for file %s (id: %s)", runs["file_name"], ids)
        return (header, for_output)
