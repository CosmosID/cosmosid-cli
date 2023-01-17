from argparse import ArgumentParser


def directory(parser: ArgumentParser, **kwargs):
    parser.add_argument(
        "--dir",
        "-d",
        **({
            "action": "store",
            "type": str,
            "default": "",
            "help": "Output directory for a file. Default: is current directory.",
            **kwargs,
        })
    )


def concurrent_download(
    parser: ArgumentParser, no_display_kwargs=None, concurrent_downloads_kwargs=None
):
    parser.add_argument(
        "--no-display",
        **{
            "action": "store_true",
            "default": False,
            "help": "Disable displaying loading process",
            **(no_display_kwargs or {}),
        }
    )
    parser.add_argument(
        "--concurrent-downloads",
        **({
            "action": "store",
            "type": int,
            "default": None,
            "help": "Limit concurrent files downloads",
            **(concurrent_downloads_kwargs or {}),
        })
    )
