import os

from cosmosid import utils
from cliff.lister import Lister
from cosmosid.helpers import argument_validators, parser_builders

from cosmosid.helpers.exceptions import (
    NotFoundException,
    NotValidFileExtension,
    WrongFlagException,
)


class Artifacts(Lister):
    """Show Artifacts for a given file."""

    def get_parser(self, prog_name):
        parser = super(Artifacts, self).get_parser(prog_name)
        parser.add_argument(
            "--run_id",
            "-r",
            action="store",
            type=argument_validators.uuid,
            help="ID of a sample run",
            required=True,
        )

        parser.add_argument(
            "--type",
            "-t",
            choices=["fastqc-zip", "champ-supplementary"],
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
        parser_builders.directory(parser)

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
            output_dir = os.path.expanduser(os.path.normpath(output_dir))
            if not os.path.isdir(output_dir):
                raise NotFoundException(
                    f"Destination directory does not exist: {output_dir}"
                )
        if output_file:
            output_file = os.path.expanduser(os.path.normpath(output_file))
            file_dir, _ = os.path.split(output_file)
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
