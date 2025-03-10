#!/usr/bin/env python
import logging.config
import os
import sys
import tempfile

import yaml
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.complete import CompleteCommand
from cliff.help import HelpAction, HelpCommand
from cosmosid import __version__
from cosmosid.client import CosmosidApi


class CosmosidApp(App):
    """Command line interface based on openstack/cliff."""
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(CosmosidApp, self).__init__(
            description="""Client for interacting with the CosmosID""",
            version=__version__,
            command_manager=CommandManager("cosmosid"),
            deferred_help=True,
        )
        self.cosmosid = None

    def build_option_parser(self, description, version, argparse_kwargs=None):
        """CMD arguments parser."""
        parser = super(CosmosidApp, self).build_option_parser(description, version, argparse_kwargs)
        parser.add_argument("--api_key", required=False, help="api key")
        parser.add_argument(
            "--base_url", required=False, help="CosmosID API base url"
        )
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
        # super(CosmosidApp, self).initialize_app(argv)
        if not argv:
            self._print_help()

    def prepare_to_run_command(self, cmd):
        super(CosmosidApp, self).prepare_to_run_command(cmd)
        if self.options.base_url and not self.options.base_url.startswith('http'):
            self.options.base_url = 'https://' + self.options.base_url
        if not isinstance(cmd, (HelpCommand, CompleteCommand)) and not self.cosmosid:
            self.cosmosid = CosmosidApi(
                api_key=self.options.api_key, base_url=self.options.base_url
            )


def main(argv=None):
    """Module entry-point."""
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
    log_conf = os.path.join(__location__, "logger_config.yaml")
    with open(log_conf, "rt") as conf_fl:
        config = yaml.safe_load(conf_fl.read())
    try:
        log_file = config["handlers"]["logfile"]["filename"]
        temp_dir = tempfile.gettempdir()
        config["handlers"]["logfile"]["filename"] = os.path.join(temp_dir, log_file)
    except KeyError:
        pass
    logging.config.dictConfig(config)
    cosmosid = CosmosidApp()
    return cosmosid.run(argv)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        pass
