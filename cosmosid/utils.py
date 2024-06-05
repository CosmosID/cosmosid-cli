import calendar
import logging
import math
import os
import sys
import threading
import time
import traceback
import typing
import uuid
import re
from datetime import datetime as dt
from functools import wraps

import requests
from cosmosid.helpers.exceptions import ValidationError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

do_not_retry_event = threading.Event()
LOCK = threading.Lock()
LOGGER = logging.getLogger(__name__)
cli_log = logging.getLogger("cosmosid.cli")


def log_traceback(ex):
    tb_lines = [
        line.strip("\n")
        for line in traceback.format_exception(ex.__class__, ex, ex.__traceback__)
    ]
    LOGGER.info(tb_lines[-1])
    LOGGER.debug("", exc_info=True)
    sys.exit(1)

def is_uuid(value):
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValidationError("Invalid UUID: {}".format(value))

def sanitize_name(fs_name):
    """
    Validates the given file system name.

    The file system name should only contain:
    _letters, numbers, dashes, underscores, and periods._
    If the name contains multiple chunks separated by spaces, 
    each chunk is validated individually and then joined back with spaces.

    Args:
        fs_name (str): The file system name to be validated.

    Returns:
        str: The validated file system name.

    Raises:
        ValueError: If the file system name is invalid.

    """
    # split name by spaces, validate each chunk and join back with spaces    
    fs_name = fs_name.strip()
    chunks = fs_name.split(" ")
    r_name = re.compile(r"^[a-zA-Z0-9_\-.]+$")    
    format_err = "Invalid format: can contain only letters, numbers, dashes, underscores and periods."
    if len(chunks) > 1:
        new_name = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue            
            if not r_name.match(chunk):
                raise ValueError(format_err)
            new_name.append(chunk)
        fs_name = " ".join(new_name)
    elif not r_name.match(fs_name):
        raise ValueError(format_err)
    return fs_name

def key_len(value, type_="ApiKey"):
    """Ensure an API Key or ID has valid length."""
    if value is not None and len(value) < 36:
        len_value = len(value)
        raise ValidationError(
            "{} must be 36 characters long, "
            "not {}".format(type_.upper(), str(len_value))
        )
    else:
        return value


def collapse_path(path):
    """Convert a path back to ~/ from expanduser()."""
    home_dir = os.path.expanduser("~")
    abs_path = os.path.abspath(path)
    return abs_path.replace(home_dir, "~")


def is_file(string):
    return bool(os.path.exists(string))


def convert_size(size):
    if size == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(size, 1024)))
    power = math.pow(1000, index)
    size = round(size / power, 3)
    return "{}{}".format(size, size_name[index])


def convert_date(date):
    utc_time_tuple = time.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
    local_time = calendar.timegm(utc_time_tuple)
    return dt.fromtimestamp(local_time).strftime("%Y-%m-%d %H:%M:%S")


def retry(
        exception_to_check=Exception,
        tries=4,
        delay=3,
        backoff=2,
        logger=None,
        raise_error=False,
):
    """Retry calling the decorated function using an exponential backoff.

    :param exception_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :type logger: logging.Logger instance
    """

    def deco_retry(func):
        @wraps(func)
        def f_retry(*args, **kwargs):
            nonlocal delay

            if do_not_retry_event.is_set():
                return

            exception = ValueError(
                "tries must me positive number greater than 0!")
            for _ in range(tries):
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    return
                except exception_to_check as error:
                    msg = "\r%s, Retrying in %d seconds.." % (
                        str(error), delay)
                    with LOCK:
                        sys.stdout.write(msg)
                        sys.stdout.flush()
                    time.sleep(delay)
                    delay *= backoff
                    exception = error
            if raise_error:
                raise exception

        return f_retry  # true decorator

    return deco_retry


def requests_retry_session(
        retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None
):
    session = session or requests.Session()
    retry_handle = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry_handle)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def progress(count, total, status=""):
    length = 60
    completed = int(round(length * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = "=" * completed + "-" * (length - completed)
    sys.stdout.write("[%s] %s%s ...%s\r" % (bar, percents, "%", status))
    sys.stdout.flush()


def get_valid_name(value, allowed_exta='_-.'):
    res = ''
    add_underscore = False
    for symbol in value:
        if symbol.isalnum() or symbol in allowed_exta:
            if add_underscore:
                add_underscore = False
                if res and res[-1] not in allowed_exta and symbol not in allowed_exta:
                    res += '_'
            res += symbol
        elif res[-1] not in allowed_exta:
            add_underscore = True
    return res


def get_table_from_json(data: typing.List[typing.Dict], columns=None, default=''):
    if columns is None:
        columns = list(data[0].keys())
    return (
        columns,
        (
            [
                [rec.get(column, default) for column in columns]
                for rec in data
            ]
        )
    )
