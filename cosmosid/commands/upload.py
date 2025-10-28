import os
import re
from pathlib import Path
from distutils.version import StrictVersion

from cliff.command import Command
from cosmosid.helpers import parser_builders, argument_actions, argument_validators
from cosmosid.helpers.exceptions import (
    CosmosidConnectionError,
    CosmosidServerError,
    AuthenticationFailed,
    ValidationError,
)
from cosmosid.enums import (
    AMPLICON_PRESETS,
    HOST_REMOVAL_OPTIONS,
    FILE_TYPES,
    Workflows,
    CLI_NAME_TO_WF_NAME,
)


class WorkflowRegistry:
    """Registry to organize workflows by type for parameter handling."""

    # Workflow categorization by type
    LONG_READ_WORKFLOWS = {
        # 16S/18S workflows that require database selection
        Workflows.LongRead16s18sPackage,
        Workflows.LongRead16s18sGreengenes2Amplicon,
        Workflows.LongRead16s18sSilvaAmplicon,
        Workflows.LongRead16s18sGtdbSsu220Amplicon,
        Workflows.LongRead16s18sEmuDefaultAmplicon,
        Workflows.LongRead16s18sMidasAmplicon,
        Workflows.LongRead16s18sHomdAmplicon,
        # ITS and Full Length rRNA workflows
        Workflows.LongReadItsAmplicon,
        Workflows.FullLengthRrnaAmplicon,
    }

    # Workflows that require database selection (only the generic 16S/18S package)
    DATABASE_REQUIRING_WORKFLOWS = {
        Workflows.LongRead16s18sPackage,
    }

    # Amplicon workflows that require primers
    AMPLICON_WORKFLOWS = {
        Workflows.AmpliseqBatchGroup,
    }

    # Database options available ONLY for LongRead16s18sPackage workflow
    # These are the unique database choices that users can select for the generic package workflow
    # Other workflows (LongRead16s18sGreengenes2Amplicon, etc.) are already bound to specific databases
    LONGREAD_16S18S_PACKAGE_DATABASE_OPTIONS = [
        {"key": "lr-greengenes2", "label": "GreenGenes2", "params_key": "gg2"},
        {"key": "lr-silva", "label": "SILVA", "params_key": "silva"},
        {"key": "lr-gtdb", "label": "GTDB SSU 220", "params_key": "gtdb_ssu_220"},
        {"key": "lr-emu", "label": "EMU Default", "params_key": "emu"},
        {"key": "lr-midas", "label": "MIDAS", "params_key": "midas"},
        {"key": "lr-homd", "label": "HOMD", "params_key": "homd"},
    ]



    @classmethod
    def get_long_read_workflows(cls, workflow_ids):
        """Filter to get only long read workflows from a list."""
        return [wf for wf in workflow_ids if wf in cls.LONG_READ_WORKFLOWS]

    @classmethod
    def get_amplicon_workflows(cls, workflow_ids):
        """Filter to get only amplicon workflows from a list."""
        return [wf for wf in workflow_ids if wf in cls.AMPLICON_WORKFLOWS]

    @classmethod
    def get_database_requiring_workflows(cls, workflow_ids):
        """Filter to get only database-requiring workflows from a list."""
        return [wf for wf in workflow_ids if wf in cls.DATABASE_REQUIRING_WORKFLOWS]


class LongReadArgumentPropagator:
    """Handles adding long read arguments to the argument parser."""

    LONG_READ_ARGS = [
        {"key": "min-length", "default": 1200, "help": "Only for Long Read workflow. Minimum length"},
        {"key": "max-length", "default": 10000, "help": "Only for Long Read workflow. Maximum length"},
        {"key": "min-quality", "default": 17, "help": "Only for Long Read workflow. Minimum quality"},
        {
            "key": "mm2-seq-type",
            "default": "map-ont",
            "help": "Only for Long Read workflow. Alignment Preset settings",
            "choices": ["map-ont", "map-hifi"],
        },
        {"key": "max-iterations", "default": 20, "help": "Only for Long Read workflow. Maximum EM iterations"},
        {"key": "probability-cutoff", "default": 0.9, "help": "Only for Long Read workflow. Probability cutoff"},
        {"key": "identity-threshold", "default": 0.9, "help": "Only for Long Read workflow. Identity threshold"},
    ]

    @classmethod
    def add_database_args(cls, parser):
        """Add database selection argument for LongRead16s18sPackage workflow only."""
        # Get available database keys and labels for help text
        db_options = WorkflowRegistry.LONGREAD_16S18S_PACKAGE_DATABASE_OPTIONS
        help_text = "Only for LongRead (16s/18s) Package workflow. Select databases for 16S/18S Long Read analysis (comma-separated, maximum 2).\n"
        help_text += "Available options:\n"
        for db in db_options:
            help_text += f"  {db['params_key']:<15} - {db['label']}\n"
        help_text += "Example: --lr-ref gg2,midas"
        
        parser.add_argument(
            "--lr-ref",
            type=str,
            help=help_text,
            default=None,
        )

    @classmethod
    def add_long_read_args(cls, parser):
        """Add common long read arguments."""
        for arg in cls.LONG_READ_ARGS:
            parser.add_argument(
                f"--{arg['key']}",
                type=type(arg["default"]),
                default=arg["default"],
                help=arg["help"],
                choices=arg.get("choices", None),
            )


class AmpliconArguments:
    """Handles adding amplicon/primer arguments to the argument parser."""

    @classmethod
    def register_args(cls, parser):
        """Add primer-related arguments."""
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
            help="Only for 'ampliseq' workflow"
            + "\n".join(
                [
                    f"""{preset_name}:
                    - forward_primer: {preset_value["forward_primer"]}
                    - reverse_primer: {preset_value["reverse_primer"]}
                """
                    for preset_name, preset_value in AMPLICON_PRESETS.items()
                ]
            ),
            type=str,
            default=None,
        )


class LongReadArgumentValidator:
    """Validates long read workflow arguments."""

    @classmethod
    def validate(cls, parsed_args, workflow_ids):
        """Validate database selection for workflows that require it."""
        db_requiring_workflows = WorkflowRegistry.get_database_requiring_workflows(workflow_ids)

        if db_requiring_workflows:
            if not parsed_args.lr_ref:
                raise ValidationError("You must specify at least 1 database using --lr-ref for LongRead16s18sPackage workflow.")
            
            # Parse comma-separated database references
            requested_databases = [db.strip() for db in parsed_args.lr_ref.split(",")]
            
            # Validate database choices
            valid_databases = {db["params_key"] for db in WorkflowRegistry.LONGREAD_16S18S_PACKAGE_DATABASE_OPTIONS}
            invalid_databases = [db for db in requested_databases if db not in valid_databases]
            
            if invalid_databases:
                valid_options = ", ".join(sorted(valid_databases))
                raise ValidationError(f"Invalid database references: {', '.join(invalid_databases)}. "
                                    f"Valid options are: {valid_options}")
            
            if len(requested_databases) > 2:
                raise ValidationError("You can select up to 2 databases for 16S/18S Long Read analysis.")
            
            return requested_databases
        return []


class AmpliconArgumentValidator:
    """Validates amplicon workflow arguments."""

    @classmethod
    def validate(cls, parsed_args, workflow_ids):
        """Validate primer arguments and return forward/reverse primers."""
        forward_primer = None
        reverse_primer = None

        # Check if any workflow requires primers (amplicon workflows)
        amplicon_workflows = WorkflowRegistry.get_amplicon_workflows(workflow_ids)

        if amplicon_workflows:
            # Validate required arguments
            if not (parsed_args.amplicon_preset or (parsed_args.forward_primer and parsed_args.reverse_primer)):
                raise ValidationError(
                    "Next arguments are required for Amplicon workflows: "
                    "`--amplicon-preset` or `--forward-primer` with `--reverse-primer`"
                )

        # Check if primer arguments are used with non-supporting workflows
        if parsed_args.amplicon_preset or parsed_args.forward_primer or parsed_args.reverse_primer:
            if not amplicon_workflows:
                raise ValidationError(
                    "Primer arguments are only available for Amplicon workflows: "
                    "`--amplicon-preset`, `--forward-primer`, `--reverse-primer`"
                )

            # Validate mutually exclusive arguments
            if parsed_args.amplicon_preset and (parsed_args.forward_primer or parsed_args.reverse_primer):
                raise ValidationError("--amplicon-preset cannot be used with forward or reverse primers")

            # Set primers based on arguments
            if parsed_args.amplicon_preset:
                forward_primer = AMPLICON_PRESETS[parsed_args.amplicon_preset]["forward_primer"]
                reverse_primer = AMPLICON_PRESETS[parsed_args.amplicon_preset]["reverse_primer"]
            else:
                if parsed_args.forward_primer:
                    forward_primer = parsed_args.forward_primer
                if parsed_args.reverse_primer:
                    reverse_primer = parsed_args.reverse_primer

        return forward_primer, reverse_primer


class LongReadWorkflowParamBuilder:
    """Exports validated long read arguments to workflow parameters."""

    @classmethod
    def build_parameters(cls, parsed_args, workflow_ids, validated_databases):
        """Export long read parameters for workflows that support them."""
        workflow_params = {}

        # Check if any workflow supports long read parameters
        long_read_workflows = WorkflowRegistry.get_long_read_workflows(workflow_ids)

        if long_read_workflows:
            workflow_params["min_length"] = parsed_args.min_length
            workflow_params["max_length"] = parsed_args.max_length
            workflow_params["min_quality"] = parsed_args.min_quality
            workflow_params["mm2_seq_type"] = parsed_args.mm2_seq_type
            workflow_params["max_iterations"] = parsed_args.max_iterations
            workflow_params["probability_cutoff"] = parsed_args.probability_cutoff
            workflow_params["identity_threshold"] = parsed_args.identity_threshold

            # Add database parameters if validated
            if validated_databases:
                workflow_params["databases"] = validated_databases

        return workflow_params


class AmpliseqWorkflowParamBuilder:
    """Exports validated amplicon arguments to workflow parameters."""

    @classmethod
    def build_parameters(cls, forward_primer, reverse_primer):
        """Export primer parameters."""
        return {
            "forward_primer": forward_primer,
            "reverse_primer": reverse_primer,
        }


class AmpliconWorkflowHelper:
    """Legacy helper class for amplicon workflow primer handling."""

    @classmethod
    def validate_and_get_primers(cls, parsed_args, workflow_ids):
        """Validate primer arguments and return forward/reverse primers."""
        return AmpliconArgumentValidator.validate(parsed_args, workflow_ids)


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
            "/path/file1.fasta -f /path/file2.fn ".format(", ".join(self.allowed_extensions)),
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
            "--max-concurrency",
            type=int,
            default=4,
            help="Max parallel part uploads (default 4)",
        )
        parser.add_argument(
            "--part-size-mb",
            type=int,
            default=6,
            help="Multipart part size in MB (min 4; default 6)",
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
            "--fastqc-only",
            help="Run only FastQC workflow",
            action="store_true",
            default=False,
        )

        # Primer arguments are now added by AmpliconArgumentPropagator

        host_removal_options_text = "\n".join([f"{key:<30}- {label}" for key, label in HOST_REMOVAL_OPTIONS.items()])
        parser.add_argument(
            "--host-name",
            help="Name for host removal.\n*Available only for type `metagenomics`\n" + host_removal_options_text,
            type=str,
            choices=HOST_REMOVAL_OPTIONS.keys(),
            default=None,
        )

        parser_builders.directory(
            parser,
            help="directory with files for upload e.g. cosmosid upload -d /path/my_dir",
        )

        # Add workflow-specific arguments using the new propagators
        LongReadArgumentPropagator.add_database_args(parser)
        LongReadArgumentPropagator.add_long_read_args(parser)
        AmpliconArguments.register_args(parser)

        # Add cross-argument validation by wrapping parse_args
        original_parse_args = parser.parse_args
        
        def validated_parse_args(*args, **kwargs):
            namespace = original_parse_args(*args, **kwargs)
            self._validate_parsed_arguments(namespace, parser)
            return namespace
        
        parser.parse_args = validated_parse_args
        return parser

    def _validate_parsed_arguments(self, namespace, parser):
        """Validate cross-argument dependencies after parsing."""
        
        # Validate workflow-specific requirements
        if hasattr(namespace, 'workflow') and namespace.workflow:
            workflows = namespace.workflow.split(',')
            workflow_ids = []  # We'll need to convert workflow names to IDs for validation
            
            # Convert workflow names to workflow IDs for validation
            for wf in workflows:
                # Remove version if present and check for specific workflows
                if 'long_read_16s18s_package' in wf:
                    workflow_ids.append(Workflows.LongRead16s18sPackage)
                elif 'ampliseq' in wf:
                    workflow_ids.append(Workflows.AmpliseqBatchGroup)
            
            # Use LongReadArgumentValidator for lr-ref validation
            try:
                LongReadArgumentValidator.validate(namespace, workflow_ids)
            except ValidationError as e:
                # Convert ValidationError to parser error for proper CLI formatting
                parser.error(str(e))
            
            # Use AmpliconArgumentValidator for primer validation
            try:
                AmpliconArgumentValidator.validate(namespace, workflow_ids)
            except ValidationError as e:
                # Convert ValidationError to parser error for proper CLI formatting
                parser.error(str(e))

    def _prepare_workflow_parameters(self, parsed_args, workflow_ids):
        """Prepare workflow parameters as a ready-to-use dictionary {workflow_id: parameters}."""
        workflow_parameters = {}
        
        # Handle amplicon workflow parameters
        amplicon_workflows = WorkflowRegistry.get_amplicon_workflows(workflow_ids)
        if amplicon_workflows:
            # Get primer parameters directly from parsed_args (validation already done in parser)
            forward_primer, reverse_primer = self._get_primer_parameters(parsed_args)
            amplicon_params = AmpliseqWorkflowParamBuilder.build_parameters(forward_primer, reverse_primer)
            for workflow_id in amplicon_workflows:
                workflow_parameters[workflow_id] = amplicon_params
        
        # Handle long read workflow parameters
        long_read_workflows = WorkflowRegistry.get_long_read_workflows(workflow_ids)
        if long_read_workflows:
            for workflow_id in long_read_workflows:
                # Get base long read parameters
                base_params = self._get_long_read_parameters(parsed_args, workflow_id)                
                workflow_parameters[workflow_id] = base_params
        
        return workflow_parameters
    
    def _get_primer_parameters(self, parsed_args):
        """Extract primer parameters from parsed arguments."""
        if parsed_args.amplicon_preset:
            preset = AMPLICON_PRESETS[parsed_args.amplicon_preset]
            return preset["forward_primer"], preset["reverse_primer"]
        else:
            return parsed_args.forward_primer, parsed_args.reverse_primer
    
    def _get_long_read_parameters(self, parsed_args, workflow_id):
        """Extract long read parameters from parsed arguments."""
        base_params =  {
            "min_length": parsed_args.min_length,
            "max_length": parsed_args.max_length,
            "min_quality": parsed_args.min_quality,
            "mm2_seq_type": parsed_args.mm2_seq_type,
            "max_iterations": parsed_args.max_iterations,
            "probability_cutoff": parsed_args.probability_cutoff,
            "identity_threshold": parsed_args.identity_threshold,
        }
        
        if workflow_id == Workflows.LongReadItsAmplicon:            
            base_params["database"] = "long_read_unite"
        
        if workflow_id == Workflows.FullLengthRrnaAmplicon:
            base_params["database"] = "long_read_rrn"
        
        if workflow_id == Workflows.LongRead16s18sPackage and parsed_args.lr_ref:
            databases = [db.strip() for db in parsed_args.lr_ref.split(",")]
            base_params["databases"] = databases

        return base_params

    def take_action(self, parsed_args):
        """Send files to analysis."""

        parent_id = parsed_args.parent if parsed_args.parent else None
        directory = parsed_args.dir if parsed_args.dir else None
        files = parsed_args.file if parsed_args.file else None
        fastqc_only = parsed_args.fastqc_only

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
                self.app.logger.info("\nReading files from directory {directory}".format(directory=directory))
            else:
                raise Exception("\nSpecified path {directory} is not a directory.".format(directory=directory))
        workflow_ids = []
        if fastqc_only:
            self.app.logger.info("\nOnly FastQC workflow will be run, workflow parameter is ignored.")
        else:
            for wf in parsed_args.workflow.split(","):
                try:
                    wf_name, wf_version, *_ = (wf + ":").split(":")

                    version_to_wf = {
                        workflow["version"]: workflow
                        for workflow in filter(
                            lambda x: x["name"] == CLI_NAME_TO_WF_NAME.get(wf_name, wf_name),
                            enabled_workflows,
                        )
                    }

                    wf_version = wf_version or max(version_to_wf.keys(), key=StrictVersion)
                    wf = version_to_wf.get(wf_version)
                    if not wf:
                        raise Exception(f"Workflow version {wf_version} is not available for {wf_name}")

                    workflow_ids.append(wf["id"])
                except IndexError as e:
                    raise Exception(f"'{wf}' workflow is not enabled") from e

            if not workflow_ids:
                raise RuntimeError(
                    f"All workflows from the given list '{parsed_args.workflow}' are not enabled, file(s) cannot be uploaded. Aborting."
                )

        # Prepare workflow parameters as ready-to-use dictionary {workflow_id: parameters}
        workflow_parameters = self._prepare_workflow_parameters(parsed_args, workflow_ids)

        pairs = []
        files = sorted(files)
        prev_fname, prev_ext = self.get_base_file_name_and_extension(files[0])

        if prev_ext not in self.allowed_extensions:
            raise Exception("not supported file extension for file {}".format(files[0]))

        paired_ended = {"files": [files[0]], "sample_name": prev_fname, "ext": prev_ext}
        for fname in files[1:]:
            cur_fname, cur_ext = self.get_base_file_name_and_extension(fname)

            if cur_ext not in self.allowed_extensions:
                raise Exception("not supported file extension for file {}".format(fname))

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
                    "file_sizes": [sum([os.path.getsize(f) for f in pair["files"] if os.path.exists(f)])],
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
            workflow_ids=workflow_ids,
            pairs=pairs,
            file_type=parsed_args.type,
            parent_id=parent_id,
            host_name=parsed_args.host_name,
            workflow_parameters=workflow_parameters,
            concurrency=parsed_args.max_concurrency,
            part_size_mb=parsed_args.part_size_mb,
        )
        self.app.logger.info("\nFiles have been sent to analysis.")
        self.app.logger.info("Task Done")
