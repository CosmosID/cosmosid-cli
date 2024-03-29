import argparse
import calendar
import logging
import os
import re
import time
import uuid
from datetime import datetime as dt
from operator import itemgetter
from os import listdir
from os.path import expanduser, isdir, isfile, join, normpath, split
from pathlib import Path

from cliff.command import Command
from cliff.lister import Lister

import cosmosid.utils as utils
from cosmosid.helpers.exceptions import (
    NotFoundException,
    NotValidFileExtension,
    WrongFlagException,
)

LOGGER = logging.getLogger(__name__)

def validate_uuid(param):
    try:
        return str(uuid.UUID(param))
    except Exception:
        raise argparse.ArgumentTypeError("Not a valid UUID!")


class ChoicesAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.choices.get(values, self.default))


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
                LOGGER.info(f"\nFolder {parent} is empty")
                for_output = [[" ", " ", " ", " ", " ", " "]]
                return (header, for_output)
        else:
            raise Exception("Exception accured.")

        def _set_date(input_date):
            try:
                utc_time_tuple = time.strptime(input_date[1], "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                utc_time_tuple = time.strptime(input_date[1], "%Y-%m-%dT%H:%M:%S")
            local_time = calendar.timegm(utc_time_tuple)
            return dt.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")

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
        LOGGER.info(f"\nContent of the Folder {parent}")
        return (header, for_output)


class Upload(Command):
    """Upload files to cosmosid."""

    allowed_extensions = [
        "fasta",
        "fna",
        "fasta.gz",
        "fastq",
        "fq",
        "fastq.gz",
        "bam",
        "sra",
    ]

    @staticmethod
    def get_base_file_name_and_extension(full_name):
        path = Path(full_name)
        file_name = path.name
        # it is needed to handle all suffixes, to be able to work with archives
        extension = "".join(path.suffixes)[1:]
        base_name = file_name.replace(extension, "")
        """Regex to match identificators in file name, which define paired-end samples.
           For example: Bacteria_x_R1.fastq Bacteria_x_R2.fastq  -- this two files must be uploaded as one file
           with name Bacteria_x. R1 and R2 endings and also L1 and L2 defines paired-end samples.
        """
        paired_end_files_suffix = r"^(.+?)(_R[12]|_R[12]_001|_L\d\d\d_R[12]|_L\d\d\d_R[12]_001|)((?:\.\w+){,2})$"
        paired_end_file_base_name = re.match(paired_end_files_suffix, file_name)
        if paired_end_file_base_name:
            return paired_end_file_base_name.group(1), extension
        return base_name, extension

    def get_parser(self, prog_name):
        parser = super(Upload, self).get_parser(prog_name)
        parser.add_argument(
            "--file",
            "-f",
            action="append",
            required=False,
            type=str,
            help="file(s) for upload. Supported file types: {} e.g. cosmosid upload -f "
            "/path/file1.fasta -f /path/file2.fn ".format(
                ", ".join(self.allowed_extensions)
            ),
        )
        parser.add_argument(
            "--parent",
            "-p",
            action="store",
            required=False,
            type=str,
            help="cosmosid parent folder ID for upload",
        )
        file_type_choice = {"metagenomics": 2, "amplicon-16s": 5, "amplicon-its": 6}
        parser.add_argument(
            "--type",
            "-t",
            action=ChoicesAction,
            required=True,
            choices=file_type_choice,
            type=str,
            default=None,
            help="Type of analysis for a file",
        )

        parser.add_argument(
            "-wf",
            "--workflow",
            help="Workflow: taxa, amr_vir, functional, amplicon_16s, amplicon_its."
                 "To specify multiple workflows, define them coma separated without any additional symbols."
                 "For example: -wf amr_vir,taxa",
            type=str,
            default="taxa",
        )
        parser.add_argument(
            "--dir",
            "-d",
            action="store",
            required=False,
            type=str,
            help="directory with files for upload e.g. cosmosid upload -d /path/my_dir",
        )

        return parser

    def take_action(self, parsed_args):
        """Send files to analysis."""

        parent_id = parsed_args.parent if parsed_args.parent else None
        directory = parsed_args.dir if parsed_args.dir else None
        files = parsed_args.file if parsed_args.file else None
        input_workflow = parsed_args.workflow
        enabled_workflows = self.app.cosmosid.get_enabled_workflows()

        profile = self.app.cosmosid.profile()
        balance = profile.get("credits", 0) + profile.get("bonuses", 0)

        if balance <= 0:
            LOGGER.info("\nYou don't have enough credits and bonuses to run analysis")
            return

        if (files and directory) or (not files and not directory):
            LOGGER.info(
                "\nInvalid input parameters. Files or directory must be specified."
                " It is not permitted to specify both file and directory in one command."
            )
            return
        elif files:
            if not all([os.path.exists(f) for f in files]):
                LOGGER.error("Not all specified files exist: %s", files)
                return
        else:
            if isdir(directory):
                files = [
                    join(directory, f)
                    for f in listdir(directory)
                    if isfile(join(directory, f))
                ]
                LOGGER.info(
                    "\nReading files from directory {directory}".format(
                        directory=directory
                    )
                )
            else:
                LOGGER.info(
                    "\nSpecified path {directory} is not a directory.".format(
                        directory=directory
                    )
                )
                return

        workflow_ids = []
        for wf in input_workflow.split(","):
            try:
                workflow_ids.append(
                    list(filter(lambda x: x["name"] == wf, enabled_workflows))[0]["id"]
                )
            except IndexError:
                LOGGER.error(f"'{wf}' workflow is not enabled")

        if not workflow_ids:
            raise RuntimeError(
                f"All workflows from the given list '{input_workflow}' are not enabled, file(s) cannot be uploaded. Aborting."
            )

        pairs = []
        files = sorted(files)
        prev_fname, prev_ext = self.get_base_file_name_and_extension(files[0])

        if prev_ext not in self.allowed_extensions:
            LOGGER.info("not supported file extension for file {}".format(files[0]))
            return
        paired_ended = {"files": [files[0]], "sample_name": prev_fname, "ext": prev_ext}
        for fname in files[1:]:
            cur_fname, cur_ext = self.get_base_file_name_and_extension(fname)

            if cur_ext not in self.allowed_extensions:
                LOGGER.info("not supported file extension for file {}".format(fname))
                return
            if cur_fname == prev_fname and prev_ext == cur_ext:
                paired_ended["files"].append(fname)
            else:
                pairs.append(paired_ended)
                paired_ended = {
                    "files": [fname],
                    "sample_name": cur_fname,
                    "ext": cur_ext,
                }
                prev_fname = cur_fname
                prev_ext = cur_ext

        pairs.append(paired_ended)
        pricing_req = []
        for pair in pairs:
            pricing_req.append(
                {
                    "sample_key": pair["sample_name"],
                    "extension": pair["ext"],
                    "file_sizes": [
                        sum(
                            [
                                os.path.getsize(f)
                                for f in pair["files"]
                                if os.path.exists(f)
                            ]
                        )
                    ],
                }
            )
        cost = 0

        for price in self.app.cosmosid.pricing(data=pricing_req):
            cost += price["pricing"][str(parsed_args.type)]
        if cost > balance:
            LOGGER.info("\nYou don't have enough credits and bonuses to run analysis")
            return

        LOGGER.info("\nFiles uploading is started")
        for pair in pairs:
            # In case some file don't have pair, we get this file and upload it as single sample
            if len(pair.get("files")) == 1:
                pair.update(sample_name=os.path.basename(pair.get("files")[0]))
            self.app.cosmosid.import_workflow(
                workflow_ids, pair, parsed_args.type, parent_id
            )
        LOGGER.info("\nFiles have been sent to analysis.")
        LOGGER.info("Task Done")


class Analysis(Lister):
    """Show Analysis for a given file."""

    def get_parser(self, prog_name):
        parser = super(Analysis, self).get_parser(prog_name)
        parser.add_argument("--id", "-i", action="store", type=validate_uuid, help="ID of a file")
        parser.add_argument(
            "--run_id", "-r", action="store", type=validate_uuid, help="ID of a sample run"
        )
        parser.add_argument(
            "--order",
            "-o",
            choices=["database", "id", "strains", "strains_filtered", "status"],
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
        r_id = utils.key_len(parsed_args.run_id, "ID") if parsed_args.run_id else None
        
        if not f_id:
            raise Exception("File id must be specified.")

        if not r_id:
            raise Exception("Run id must be specified.")
        
        analysis_content = self.app.cosmosid.analysis_list(file_id=f_id, run_id=r_id)
        header = ["id", "database", "strains", "strains_filtered", "status"]
        if analysis_content:
            if not analysis_content["analysis"]:
                LOGGER.info(
                    "\nThere are no analysis for run id %s", analysis_content["run_id"]
                )

                for_output = [[" ", " ", " ", " ", " "]]
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
            return dt.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")

        def _del_none(inp):
            out = inp[1]
            if not out:
                out = 0 if field_maps[inp[0]][1] == "int" else "-"
            return out

        def _convert(inp):
            database = inp["database"]
            db_description = database["description"]
            for item in inp.items():
                for k, v in field_maps.items():
                    if item[0] == v[0]:
                        inp[item[0]] = (
                            field_maps[k][2](item)
                            if item[0] != "database"
                            else db_description
                        )
                        break
            return inp

        field_maps = {
            "id": ["id", "str", _del_none],
            "database": ["database", "str", _del_none],
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
            LOGGER.info(
                "Run ID is not entered. Analysis list from latest run "
                "(%s) for file %s",
                _set_date(run_metadata["created"]),
                run_metadata["file"]["name"],
            )

        LOGGER.info(
            "\nAnalysis list for file %s and run id %s (%s)",
            run_metadata["file"]["name"],
            run_metadata["id"],
            _set_date(run_metadata["created"]),
        )
        return (header, for_output)


class Reports(Command):
    """Get analysis reports TSV"""

    def get_parser(self, prog_name):
        parser = super(Reports, self).get_parser(prog_name)
        parser.add_argument(
            "--id",
            "-i",
            action="store",
            required=True,
            type=validate_uuid,
            help="ID of cosmosid sample.",
        )
        grp = parser.add_mutually_exclusive_group(required=False)
        grp.add_argument(
            "--output",
            "-o",
            action="store",
            type=str,
            help="output file name. Must have .zip extension. \
                               Default: is equivalent to cosmosid file name.",
        )
        grp.add_argument(
            "--dir",
            "-d",
            action="store",
            type=str,
            help="output directory for a file. \
                               Default: is current directory.",
        )
        return parser

    def take_action(self, parsed_args):
        """Save report to a given file."""
        f_id = utils.key_len(parsed_args.id, "ID") if parsed_args.id else None

        output_file = parsed_args.output if parsed_args.output else None
        output_dir = parsed_args.dir if parsed_args.dir else None
        response = self.app.cosmosid.report(
            file_id=f_id, output_file=output_file, output_dir=output_dir
        )
        if response:
            LOGGER.info("\nReport has been saved to: %s", response["saved_report"])
        else:
            raise Exception("Exception occurred during report creation.")
        LOGGER.info("Task Done")


class Runs(Lister):
    """Show List Of Runs for a given File."""

    def get_parser(self, prog_name):
        parser = super(Runs, self).get_parser(prog_name)
        parser.add_argument(
            "--id", "-i", type=validate_uuid, required=True, help="ID of the sample"
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
        header = ["id", "status", "created"]
        if runs:
            if not runs["runs"]:
                LOGGER.info(
                    "\nThere are no runs for sample %s (id: %s)", runs["file_name"], ids
                )

                for_output = [[" ", " ", " "]]
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
            return dt.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")

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
        for_output = [
            [item[field_maps[field][0]] for field in header] for item in runs_data
        ]
        LOGGER.info("\nRuns list for file %s (id: %s)", runs["file_name"], ids)
        return (header, for_output)


class Artifacts(Lister):
    """Show Artifacts for a given file."""

    def get_parser(self, prog_name):
        parser = super(Artifacts, self).get_parser(prog_name)
        parser.add_argument(
            "--run_id",
            "-r",
            action="store",
            type=validate_uuid,
            help="ID of a sample run",
            required=True,
        )

        parser.add_argument(
            "--type",
            "-t",
            choices=["fastqc-zip"],
            type=str,
            help="Artifact type to download",
        )

        parser.add_argument(
            "--url", action="store_true", default=False, help="show download url"
        )

        parser.add_argument(
            "--output",
            "-o",
            action="store",
            type=str,
            default=None,
            help="output file name. Must have .zip extension. \
                               Default: is equivalent to cosmosid file name.",
        )

        parser.add_argument(
            "--dir",
            "-d",
            action="store",
            type=str,
            default=None,
            help="output directory for a file. \
                               Default: is current directory.",
        )

        return parser

    def take_action(self, parsed_args):
        """get  with artifacts for a file and prepare for output"""
        run_id = utils.key_len(parsed_args.run_id, "ID")
        output_dir = parsed_args.dir
        output_file = parsed_args.output
        if not parsed_args.type and parsed_args.url:
            raise WrongFlagException("--type flag is required!")
        if (output_dir or output_file or not parsed_args.type) and parsed_args.url:
            raise WrongFlagException(
                "Can't use --url flag with --dir/-d or --output/-o flag!"
            )
        if output_dir:
            output_dir = expanduser(normpath(output_dir))
            if not isdir(output_dir):
                raise NotFoundException(
                    f"Destination directory does not exist: {output_dir}"
                )
        if output_file:
            output_file = expanduser(normpath(output_file))
            file_dir, _ = split(output_file)
            if file_dir != "":
                raise NotValidFileExtension(
                    "Not allowed to set path with --output/-o flag, If you want to set path you can use --dir/-d flag!"
                )
        return self.app.cosmosid.artifacts_list(
            artifact_type=parsed_args.type,
            run_id=run_id,
            output_file=output_file,
            output_dir=output_dir,
            url=parsed_args.url,
        )


class Samples(Lister):
    """Download Samples for a given samples ids."""

    def get_parser(self, prog_name):
        parser = super(Samples, self).get_parser(prog_name)
        parser.add_argument(
            "--samples_ids",
            "-s",
            action="store",
            type=lambda s: [validate_uuid(i) for i in re.split(",", s)],
            help="Comma separated list of samples uuids",
            required=True,
        )

        parser.add_argument(
            "--dir",
            "-d",
            action="store",
            type=str,
            default=None,
            help="Output directory for a file. Default: is current directory.",
        )
        parser.add_argument(
            "--no-display",
            action="store_true",
            default=False,
            help="Disable displaying loading process",
        )
        parser.add_argument(
            "--concurrent-downloads",
            action="store",
            type=int,
            default=None,
            help="Limit concurrent files downloads",
        )
        return parser

    def take_action(self, parsed_args):
        """get  with artifacts for a file and prepare for output"""
        samples = [
            utils.key_len(samples_id, "ID") for samples_id in parsed_args.samples_ids
        ]
        output_dir = parsed_args.dir
        if output_dir:
            output_dir = expanduser(normpath(output_dir))
            if not isdir(output_dir):
                raise NotFoundException(
                    f"Destination directory does not exist: {output_dir}"
                )
        if not output_dir:
            output_dir = os.getcwd()

        return self.app.cosmosid.download_samples(
            samples or [],
            parsed_args.concurrent_downloads,
            not parsed_args.no_display,
            output_dir,
        )
