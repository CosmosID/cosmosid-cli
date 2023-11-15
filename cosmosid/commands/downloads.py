import re
import os
from typing import List

from cliff.lister import Lister
from cosmosid.helpers import argument_validators, parser_builders
from cosmosid.helpers.exceptions import NotFoundException, ValidationError


class Downloads(Lister):
    """Download Samples for a given samples ids."""

    def __validate(self, parsed_args):
        if not (parsed_args.samples_ids or parsed_args.input_file):
            raise ValueError("Please, specify '--samples_ids' or '--input-file' option")
        elif parsed_args.samples_ids and parsed_args.input_file:
            raise ValueError("Please, specify only one of '--samples_ids', '--input-file' options")

    def get_parser(self, prog_name):
        parser = super(Downloads, self).get_parser(prog_name)
        parser.add_argument(
            "--samples_ids",
            "-s",
            action="store",
            type=lambda s: [argument_validators.uuid(i) for i in re.split(",", s)],
            help="Comma separated list of samples uuids",
            required=False,
        )
        parser.add_argument(
            "--input-file",
            action="store",
            type=str,
            help="Path to file with samples' ids",
            required=False,
        )

        parser_builders.directory(parser)
        parser_builders.concurrent_download(parser)
        return parser

    def read_samples_from_file(self, filepath: str)->List[str]:
        res = []
        with open(filepath, 'r') as file:
            for i, line in enumerate(file.readlines()):
                uuid = line.strip()
                if uuid:
                    try:
                        res.append(argument_validators.uuid(uuid))
                    except ValidationError as e:
                        raise Exception(f'Exception during reading samples from file:\nLine {i}: {e}') from e
        return res

    def take_action(self, parsed_args):
        """get  with artifacts for a file and prepare for output"""
        self.__validate(parsed_args)
        if parsed_args.samples_ids:
            samples = parsed_args.samples_ids
        else:
            samples = self.read_samples_from_file(parsed_args.input_file)

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
            samples,
            parsed_args.concurrent_downloads,
            not parsed_args.no_display,
            output_dir,
        )
