import calendar
import logging
import math
import os
import threading
import time
import sys
from datetime import datetime as dt
from functools import wraps

import traceback
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from cosmosid.helpers.exceptions import ValidationError

do_not_retry_event = threading.Event()
LOCK = threading.Lock()
LOGGER = logging.getLogger(__name__)
cli_log = logging.getLogger("cosmosid.cli")


def log_traceback(ex):
    tb_lines = [line.strip('\n') for line in
                traceback.format_exception(ex.__class__, ex, ex.__traceback__)]
    LOGGER.info(tb_lines[-1])
    LOGGER.debug('', exc_info=True)
    sys.exit(1)


def key_len(value, type_="ApiKey"):
    """Ensure an API Key or ID has valid length."""
    if value is not None and len(value) < 36:
        len_value = len(value)
        raise ValidationError('{} must be 36 characters long, '
                              'not {}'.format(type_.upper(), str(len_value)))
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
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(size, 1024)))
    power = math.pow(1024, index)
    size = round(size / power, 2)
    return '{}{}'.format(size, size_name[index])


def convert_date(date):
    utc_time_tuple = time.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
    local_time = calendar.timegm(utc_time_tuple)
    return dt.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')


def retry(exception_to_check=Exception, tries=4, delay=3, backoff=2,
          logger=None):
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
            mtries, mdelay = tries, delay
            while mtries > 1:
                if do_not_retry_event.is_set():
                    break
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    break
                except exception_to_check as error:
                    msg = "\r%s, Retrying in %d seconds.." % (str(error),
                                                              mdelay)
                    with LOCK:
                        sys.stdout.write(msg)
                        sys.stdout.flush()
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)

        return f_retry  # true decorator
    return deco_retry


def requests_retry_session(retries=3,
                           backoff_factor=0.3,
                           status_forcelist=(500, 502, 504),
                           session=None):

    session = session or requests.Session()
    retry_handle = Retry(total=retries,
                         read=retries,
                         connect=retries,
                         backoff_factor=backoff_factor,
                         status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry_handle)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
