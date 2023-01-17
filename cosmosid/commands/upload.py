import os
import re
from pathlib import Path

from cliff.command import Command
from cosmosid.helpers import parser_builders, argument_actions


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
        paired_end_file_base_name = re.match(
            paired_end_files_suffix, file_name)
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
        file_type_choice = {"metagenomics": 2,
                            "amplicon-16s": 5, "amplicon-its": 6}
        parser.add_argument(
            "--type",
            "-t",
            action=argument_actions.ChoicesAction,
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
        parser_builders.directory(
            parser,
            help="directory with files for upload e.g. cosmosid upload -d /path/my_dir"
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
            self.app.logger.info(
                "\nYou don't have enough credits and bonuses to run analysis")
            return

        if (files and directory) or (not files and not directory):
            self.app.logger.info(
                "\nInvalid input parameters. Files or directory must be specified."
                " It is not permitted to specify both file and directory in one command."
            )
            return
        elif files:
            if not all([os.path.exists(f) for f in files]):
                self.app.logger.error(
                    "Not all specified files exist: %s", files)
                return
        else:
            if os.path.isdir(directory):
                files = [
                    os.path.join(directory, f)
                    for f in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, f))
                ]
                self.app.logger.info(
                    "\nReading files from directory {directory}".format(
                        directory=directory
                    )
                )
            else:
                self.app.logger.info(
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
                self.app.logger.error(f"'{wf}' workflow is not enabled")

        if not workflow_ids:
            raise RuntimeError(
                f"All workflows from the given list '{input_workflow}' are not enabled, file(s) cannot be uploaded. Aborting."
            )

        pairs = []
        files = sorted(files)
        prev_fname, prev_ext = self.get_base_file_name_and_extension(files[0])

        if prev_ext not in self.allowed_extensions:
            self.app.logger.info(
                "not supported file extension for file {}".format(files[0]))
            return
        paired_ended = {"files": [files[0]],
                        "sample_name": prev_fname, "ext": prev_ext}
        for fname in files[1:]:
            cur_fname, cur_ext = self.get_base_file_name_and_extension(fname)

            if cur_ext not in self.allowed_extensions:
                self.app.logger.info(
                    "not supported file extension for file {}".format(fname))
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
            self.app.logger.info(
                "\nYou don't have enough credits and bonuses to run analysis")
            return

        self.app.logger.info("\nFiles uploading is started")
        for pair in pairs:
            # In case some file don't have pair, we get this file and upload it as single sample
            if len(pair.get("files")) == 1:
                pair.update(sample_name=os.path.basename(pair.get("files")[0]))
            self.app.cosmosid.import_workflow(
                workflow_ids, pair, parsed_args.type, parent_id
            )
        self.app.logger.info("\nFiles have been sent to analysis.")
        self.app.logger.info("Task Done")
