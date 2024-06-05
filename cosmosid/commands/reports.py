from cosmosid import utils
from cliff.command import Command
from cosmosid.helpers import argument_validators, parser_builders


class Reports(Command):
    """Get analysis reports TSV"""

    def get_parser(self, prog_name):
        parser = super(Reports, self).get_parser(prog_name)
        parser.add_argument(
            "--id",
            "-i",
            action="store",
            required=True,
            type=argument_validators.uuid,
            help="ID of cosmosid sample.",
        )
        parser.add_argument(
            "--timeout",
            "-t",
            action="store",
            type=int,
            default=5 * 60,
            help="The timeout in seconds. Default: 5 minutes.")
        
        grp = parser.add_mutually_exclusive_group(required=False)
        grp.add_argument(
            "--output",
            "-o",
            action="store",
            type=str,
            help="output file name. Must have .zip extension. \
                               Default: is equivalent to cosmosid file name.",
        )
        parser_builders.directory(grp)
        return parser

    def take_action(self, parsed_args):
        """Save report to a given file."""
        f_id = utils.key_len(parsed_args.id, "ID") if parsed_args.id else None

        output_file = parsed_args.output if parsed_args.output else None
        output_dir = parsed_args.dir if parsed_args.dir else None
        timeout = parsed_args.timeout
        response = self.app.cosmosid.report(
            file_id=f_id, output_file=output_file, output_dir=output_dir, timeout=timeout
        )
        if response:
            self.app.logger.info("\nReport has been saved to: %s", response["saved_report"])
        else:
            raise Exception("Exception occurred during report creation.")
        self.app.logger.info("Task Done")
