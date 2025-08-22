#!/usr/bin/env python
import logging.config
import os
import sys
import tempfile

import yaml
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.complete import CompleteCommand
from cliff.help import HelpCommand
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
        # Simplified help printing; constructing HelpAction with None parameters caused type issues.
        if self.parser:
            self.parser.print_help()

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
    # Place log file in a per-user writable location to avoid cross-user lock contention
    try:
        handler_cfg = config["handlers"]["logfile"]
        log_file = handler_cfg["filename"]
        # Determine base directory preference order for log + lock
        user_base = (
            os.environ.get("COSMOSID_LOG_DIR")
            or os.environ.get("XDG_STATE_HOME")
            or os.path.join(os.path.expanduser("~"), ".local", "state", "cosmosid")
        )
        try:
            os.makedirs(user_base, exist_ok=True)
        except Exception:
            user_base = os.path.join(tempfile.gettempdir(), f"cosmosid-{os.getuid()}")
            os.makedirs(user_base, exist_ok=True)
        handler_cfg["filename"] = os.path.join(user_base, log_file)
    except KeyError:
        pass
    logging.config.dictConfig(config)
    cosmosid = CosmosidApp()
    # Parse verbosity early to adjust root logger before commands execute
    # (cliff will parse again inside run but we want logging level debug now)
    args_list = argv or []
    debug_forced = '--debug' in args_list    
    if debug_forced:
        logging.getLogger().setLevel(logging.DEBUG)
    return cosmosid.run(argv)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        pass
