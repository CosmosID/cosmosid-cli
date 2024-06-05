from cliff.command import Command
from cosmosid import utils


class MakeDir(Command):
    """Make a new directory in a given directory."""

    def get_parser(self, prog_name):
        parser = super(MakeDir, self).get_parser(prog_name)
        parser.add_argument(
            "--parent",
            "-p",
            type=str,
            default=None,
            required=False,
            help="ID of the parent directory. Default: Root ",
        )
        parser.add_argument(
            "--name", "-n", type=str, required=True, help="Name of the new directory: [a-z,0-9,-,_,.] < 150 chars."
        )
        return parser

    def take_action(self, parsed_args):
        if parsed_args.parent is not None:
            if not utils.is_uuid(parsed_args.parent):
                raise ValueError("Invalid UUID for parent folder.")        
        # validate name (not empty, dont start/finish with empty space, no special chars except of brackets, dashes and underscores, allow spaces in the middle)
        name = utils.sanitize_name(parsed_args.name)
        if len(name) > 150:
            raise ValueError("Name should not exceed 150 chars.")
        try:
            new_folder_id = self.app.cosmosid.make_dir(
                name=name, parent_id=parsed_args.parent
            )
            self.app.logger.info(f"\nFolder {name}: {new_folder_id} has been created.")
            return 0
        except Exception as err:
            self.app.logger.error("Failed to create directory %s", name)
            utils.log_traceback(err)  # should be a better error code
