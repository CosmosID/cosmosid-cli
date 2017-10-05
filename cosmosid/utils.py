
import logging
import os
import math
from cosmosid.helpers.exceptions import ValidationError

logger = logging.getLogger(__name__)
cli_log = logging.getLogger("cosmosid.cli")


def key_len(value, type_="ApiKey"):
    """Ensure an API Key or ID has valid length."""
    if value is not None and len(value) < 36:
        l = len(value)
        raise ValidationError("{} must be 36 characters long, not {}".format(type_.upper(), str(l)))
    else:
        return value


def collapse_path(path):
    """Convert a path back to ~/ from expanduser()."""
    home_dir = os.path.expanduser("~")
    abs_path = os.path.abspath(path)
    return abs_path.replace(home_dir, "~")


def is_file(string):
    if os.path.exists(string):
        return True
    else:
        return False


def convert_size(size):
    if (size == 0):
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, index)
    s = round(size/p, 2)
    return '{}{}'.format(s, size_name[index])
