import os
import re
from pathlib import Path
from distutils.version import StrictVersion

from cliff.command import Command
from cosmosid.helpers import parser_builders, argument_actions, argument_validators
from cosmosid.enums import AMPLICON_PRESETS, HOST_REMOVAL_OPTIONS, FILE_TYPES, Workflows, CLI_NAME_TO_WF_NAME
from cosmosid.helpers.exceptions import CosmosidConnectionError, CosmosidServerError, AuthenticationFailed


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
        parser.add_argument(
            "--type",
            "-t",
            action=argument_actions.ChoicesAction,
            required=True,
            choices=FILE_TYPES,
            type=str,
            default=None,
            help="Type of analysis for a file",
        )

        parser.add_argument(
            "-wf",
            "--workflow",
            help="To specify multiple workflows, define them coma separated without any additional symbols.\n"
                 "Add :<version> if you need to specify version\n"
                 "For example: -wf taxa:1.1.0,amr_vir\n"
                 "(Latest workflow version will be used if it wasn't specified)"
                 " Use 'workflows' command to view possible workflows",
            type=str,
            default="taxa",
        )

        parser.add_argument(
            "--forward-primer",
            help="Only for 'ampliseq' workflow",
            type=argument_validators.is_primer,
            default=None,
        )
        parser.add_argument(
            "--reverse-primer",
            help="Only for 'ampliseq' workflow",
            type=argument_validators.is_primer,
            default=None,
        )
        parser.add_argument(
            "--amplicon-preset",
            choices=AMPLICON_PRESETS.keys(),
            help="Only for 'ampliseq' workflow"+'\n'.join([
                f'''{preset_name}:
                    - forward_primer: {preset_value['forward_primer']}
                    - reverse_primer: {preset_value['reverse_primer']}
                '''
                for preset_name, preset_value in AMPLICON_PRESETS.items()
            ]),
            type=str,
            default=None,
        )

        host_removal_options_text = '\n'.join([f'{key:<30}- {label}' for key, label in HOST_REMOVAL_OPTIONS.items()])
        parser.add_argument(
            "--host-name",
            help="Name for host removal.\n*Available only for type `metagenomics`\n" + host_removal_options_text,
            type=str,
            choices=HOST_REMOVAL_OPTIONS.keys(),
            default=None,
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
        
        try:
            enabled_workflows = self.app.cosmosid.get_enabled_workflows()
        except CosmosidServerError:
            self.app.logger.error("Server error occurred while getting workflows")
        except AuthenticationFailed:
            self.app.logger.error("Cannot get workflows. Ensure you use valid api-key")
        except CosmosidConnectionError:
            self.app.logger.error("Connection error occurred while getting workflows")

        profile = self.app.cosmosid.profile()
        balance = profile.get("credits", 0) + profile.get("bonuses", 0)

        if balance <= 0:
            raise Exception("\nYou don't have enough credits and bonuses to run analysis")

        if (files and directory) or (not files and not directory):
            raise Exception(
                "\nInvalid input parameters. Files or directory must be specified."
                " It is not permitted to specify both file and directory in one command."
            )
        elif files:
            if not all([os.path.exists(f) for f in files]):
                raise Exception("Not all specified files exist: %s", files)
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
                raise Exception(
                    "\nSpecified path {directory} is not a directory.".format(
                        directory=directory
                    )
                )

        workflow_ids = []
        for wf in parsed_args.workflow.split(","):
            try:
                wf_name, wf_version, *_ = (wf+':').split(':')
                
                version_to_wf = {
                    workflow['version']: workflow 
                    for workflow in filter(lambda x: x["name"] == CLI_NAME_TO_WF_NAME.get(wf_name, wf_name), enabled_workflows)
                }
                
                wf_version = wf_version or max(version_to_wf.keys(), key=StrictVersion)
                wf = version_to_wf.get(wf_version)
                if not wf:
                    raise Exception(f'Workflow version {wf_version} is not available for {wf_name}')
                
                workflow_ids.append(wf['id'])
            except IndexError as e:
                raise Exception(f"'{wf}' workflow is not enabled") from e

        if not workflow_ids:
            raise RuntimeError(
                f"All workflows from the given list '{parsed_args.workflow}' are not enabled, file(s) cannot be uploaded. Aborting."
            )

        forward_primer = None
        reverse_primer = None

        if Workflows.AmpliseqBatchGroup in workflow_ids and not (
            parsed_args.amplicon_preset or (parsed_args.forward_primer and parsed_args.reverse_primer)
        ):
            raise Exception(
                'Next arguments are required for Amplicon 16S Batch: '
                '`--amplicon-preset` or  `--forward-primer` with `--reverse-primer`'
            )
        
        if parsed_args.amplicon_preset or parsed_args.forward_primer or parsed_args.reverse_primer:
            if Workflows.AmpliseqBatchGroup not in workflow_ids:
                raise Exception (
                    'Next arguments are available only for Amplicon 16S Batch: '
                    '`--amplicon-preset`, `--forward-primer`, `--reverse-primer`'
                )
            
            if parsed_args.amplicon_preset and (parsed_args.forward_primer or parsed_args.reverse_primer):
                raise Exception('--amplicon-preset cannot be used with forward or reverse primers')
            
            if parsed_args.amplicon_preset:
                forward_primer = AMPLICON_PRESETS[parsed_args.amplicon_preset]['forward_primer']
                reverse_primer = AMPLICON_PRESETS[parsed_args.amplicon_preset]['reverse_primer']
            if parsed_args.forward_primer:
                forward_primer = parsed_args.forward_primer
            if parsed_args.reverse_primer:
                reverse_primer = parsed_args.reverse_primer

        pairs = []
        files = sorted(files)
        prev_fname, prev_ext = self.get_base_file_name_and_extension(files[0])

        if prev_ext not in self.allowed_extensions:
            raise Exception("not supported file extension for file {}".format(files[0]))

        paired_ended = {"files": [files[0]],
                        "sample_name": prev_fname, "ext": prev_ext}
        for fname in files[1:]:
            cur_fname, cur_ext = self.get_base_file_name_and_extension(fname)

            if cur_ext not in self.allowed_extensions:
                raise Exception(
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
            raise Exception("\nYou don't have enough credits and bonuses to run analysis")

        self.app.logger.info("\nFiles uploading is started")
        for pair in pairs:
            # In case some file don't have pair, we get this file and upload it as single sample
            if len(pair.get("files")) == 1:
                pair.update(sample_name=os.path.basename(pair.get("files")[0]))
        self.app.cosmosid.import_workflow(
            workflow_ids, pairs, parsed_args.type, parent_id, parsed_args.host_name, forward_primer, reverse_primer
        )
        self.app.logger.info("\nFiles have been sent to analysis.")
        self.app.logger.info("Task Done")
