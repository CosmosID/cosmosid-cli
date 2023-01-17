import re
import os

from cosmosid import utils
from cliff.lister import Lister
from cosmosid.helpers import argument_validators, parser_builders
from cosmosid.helpers.exceptions import NotFoundException


class Downloads(Lister):
    """Download Samples for a given samples ids."""

    def get_parser(self, prog_name):
        parser = super(Downloads, self).get_parser(prog_name)
        parser.add_argument(
            "--samples_ids",
            "-s",
            action="store",
            type=lambda s: [argument_validators.uuid(
                i) for i in re.split(",", s)],
            help="Comma separated list of samples uuids",
            required=True,
        )

        parser_builders.directory(parser)
        parser_builders.concurrent_download(parser)
        return parser

    def take_action(self, parsed_args):
        """get  with artifacts for a file and prepare for output"""
        samples = [
            utils.key_len(samples_id, "ID") for samples_id in parsed_args.samples_ids
        ]
        output_dir = parsed_args.dir
        if output_dir:
            output_dir = os.path.expanduser(os.path.normpath(output_dir))
            if not os.path.isdir(output_dir):
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
