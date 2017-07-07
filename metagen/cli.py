#!/usr/bin/env python

import logging
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.complete import CompleteCommand
from cliff.help import HelpCommand, HelpAction
from metagen.client import MetagenApi

"""Configuring logging."""
formatter = logging.Formatter("[%(name)s][%(levelname)s][%(asctime)s] - %(message)s")
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class MetagenApp(App):

    def __init__(self):
        super(MetagenApp, self).__init__(
            description="""Client for interacting with the CosmosID Metagen""",
            version='0.1ev1',
            command_manager=CommandManager('metagen'),
            deferred_help=True)
        self.metagen = None

    def build_option_parser(self, description, version, argparse_kwargs=None):
        """ """
        parser = super(MetagenApp, self).build_option_parser(description, version, argparse_kwargs)
        parser.add_argument(
            '--api_key',
            default=False,
            required=False,
            help='api key')
        parser.add_argument(
            '--base_url',
            default=False,
            required=False,
            help='metagen API base url')
        return parser

    def _print_help(self):
        """Generate the help string using cliff.help.HelpAction."""

        action = HelpAction(None, None, default=self)
        action(self.parser, self.options, None, None)

    def initialize_app(self, argv):
        """Overrides: cliff.app.initialize_app

        The cliff.app.run automatically assumes and starts
        interactive mode if launched with no arguments.  Short
        circuit to disable interactive mode, and print help instead.
        """
        # super(MetagenApp, self).initialize_app(argv)
        if len(argv) == 0:
            self._print_help()

    def prepare_to_run_command(self, cmd):
        super(MetagenApp, self).prepare_to_run_command(cmd)
        if not type(cmd) in (HelpCommand, CompleteCommand) and not self.metagen:
            self.metagen = MetagenApi(
                api_key=self.options.api_key,
                base_url=self.options.base_url
            )

    def clean_up(self, cmd, result, err):
        super(MetagenApp, self).clean_up(cmd, result, err)

    def run(self, argv):
        result = super(MetagenApp, self).run(argv)
        return result


def main(argv=sys.argv[1:]):
    metagen = MetagenApp()
    return metagen.run(argv)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
