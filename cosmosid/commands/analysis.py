import time
import calendar
from datetime import datetime
from operator import itemgetter

from cliff.lister import Lister
from cosmosid import utils
from cosmosid.helpers import argument_validators


class Analysis(Lister):
    """Show Analysis for a given file."""

    def get_parser(self, prog_name):
        parser = super(Analysis, self).get_parser(prog_name)
        parser.add_argument("--id", "-i", action="store",
                            type=argument_validators.uuid, help="ID of a file")
        parser.add_argument(
            "--run_id", "-r", action="store", type=argument_validators.uuid, help="ID of a sample run"
        )
        parser.add_argument(
            "--order",
            "-o",
            choices=["database", "id", "strains",
                     "strains_filtered", "status"],
            type=str,
            help="field for ordering",
        )
        parser.add_argument(
            "--up", action="store_true", default=False, help="order direction"
        )
        return parser

    def take_action(self, parsed_args):
        """get json with analysis for a file and prepare for output"""
        f_id = utils.key_len(parsed_args.id, "ID") if parsed_args.id else None
        r_id = utils.key_len(parsed_args.run_id,
                             "ID") if parsed_args.run_id else None

        if not f_id:
            raise Exception("File id must be specified.")

        if not r_id:
            raise Exception("Run id must be specified.")

        analysis_content = self.app.cosmosid.analysis_list(
            file_id=f_id, run_id=r_id)
        header = [
            "id",
            "database_name",
            "database_version",
            "strains",
            "strains_filtered",
            "status",
        ]
        if analysis_content:
            if not analysis_content["analysis"]:
                self.app.logger.info(
                    "\nThere are no analysis for run id %s", analysis_content["run_id"]
                )

                for_output = [["" for _ in header]]
                return (header, for_output)
        else:
            raise Exception("Exception occured.")

        def _set_date(inp):
            try:
                utc_time_tuple = time.strptime(inp, "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(inp, "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            # time.ctime(local_time)
            return datetime.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")

        def _del_none(inp):
            out = inp[1]
            if not out:
                out = 0 if field_maps[inp[0]][1] == "int" else "-"
            return out

        def _convert(inp):
            database = inp["database"]
            version = inp["version"]
            db_description = database["description"]
            db_version = version["database_version"]
            for item in inp.items():
                for _, v in field_maps.items():
                    if item[0] == v[0]:
                        if item[0] == "database":
                            inp[item[0]] = db_description
                        if item[0] == "version":
                            inp[item[0]] = db_version
                        break
            return inp

        field_maps = {
            "id": ["id", "str", _del_none],
            "database_name": ["database", "str", _del_none],
            "database_version": ["version", "str", _del_none],
            "status": ["status", "str", _del_none],
            "strains": ["strains", "int", _del_none],
            "strains_filtered": ["strains_filtered", "int", _del_none],
        }

        run_metadata = analysis_content["run_meta"]

        # we need just items for output
        items_data = [_convert(item) for item in analysis_content["analysis"]]

        # order regarding order parameters
        if parsed_args.order:
            if parsed_args.order.lower() in header:
                items_data = sorted(
                    items_data,
                    key=itemgetter(field_maps[parsed_args.order.lower()][0]),
                    reverse=(not parsed_args.up),
                )

        for_output = [
            [item[field_maps[field][0]] for field in header] for item in items_data
        ]

        if not r_id:
            self.app.logger.info(
                "Run ID is not entered. Analysis list from latest run "
                "(%s) for file %s",
                _set_date(run_metadata["created"]),
                run_metadata["file"]["name"],
            )

        self.app.logger.info(
            "\nAnalysis list for file %s and run id %s (%s)",
            run_metadata["file"]["name"],
            run_metadata["id"],
            _set_date(run_metadata["created"]),
        )
        return (header, for_output)
