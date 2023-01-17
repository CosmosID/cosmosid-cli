from importlib.util import find_spec
from os.path import getsize, isfile, join

from requests import Session, Timeout

from cosmosid.helpers.exceptions import (
    NonRecoverableDownloadError,
    RecoverableDownloadError,
    RangeNotSatisfiableError,
)
from cosmosid.helpers.thread_logger import ThreadLogger
from cosmosid.utils import retry

IS_PYCURL_INSTALLED = find_spec("pycurl")

if IS_PYCURL_INSTALLED:
    import pycurl


class Downloader:
    @staticmethod
    def _get_loading_line(cur, limit):
        limit = float(limit)
        length = 60
        completed = round(length * cur / limit)
        if completed >= 100:
            return "Completed"
        percents = min(round(100 * cur / limit, 1), 100)
        bar = "=" * completed + "-" * (length - completed)
        return "[%s] %s%%\tDownloading..." % (bar, percents)

    @staticmethod
    def _validate(filepath, real_size, expected_size):
        if expected_size == real_size:
            # TODO: it would be better to check hash sum
            raise FileExistsError(f"Destination File exists: {filepath}")

    @staticmethod
    def _check_status_code(status_code):
        if 500 <= status_code < 600:
            raise RecoverableDownloadError
        elif status_code == 416:
            raise RangeNotSatisfiableError
        elif 400 <= status_code < 500:
            raise NonRecoverableDownloadError

    @classmethod
    def log(cls, filename: str, loaded_size: float, total_size: float, *args, **kwargs):
        if total_size:
            ThreadLogger().info(
                filename, cls._get_loading_line(loaded_size, total_size)
            )

    @classmethod
    def get_downloader(cls):
        return (
            cls._load_file_with_curl
            if IS_PYCURL_INSTALLED
            else cls._load_file_with_requests
        )

    @classmethod
    @retry(RecoverableDownloadError, raise_error=True)
    def load_file(
        cls,
        url,
        expected_size,
        filename,
        filedir,
        chunk_size=4 * 1024**2,
        display_loading=True,
    ):
        filepath = join(filedir, filename)
        real_size = getsize(filepath) if isfile(filepath) else 0
        cls._validate(filepath, real_size, expected_size)
        cls.get_downloader()(
            url, filename, filedir, real_size, display_loading, chunk_size
        )

    @classmethod
    def _load_file_with_curl(
        cls, url, filename, filedir, real_file_size, display_loading, *args
    ):
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.RESUME_FROM, real_file_size)
        try:
            with open(
                join(filedir, filename), "ab" if real_file_size else "wb"
            ) as file:
                curl.setopt(pycurl.WRITEDATA, file)
                if display_loading:
                    curl.setopt(pycurl.NOPROGRESS, False)
                    curl.setopt(
                        pycurl.XFERINFOFUNCTION,
                        lambda total_size, loaded_size, *args, **kwargs: cls.log(
                            filename,
                            loaded_size + real_file_size,
                            float(total_size) + real_file_size if total_size else 0,
                        ),
                    )
                curl.perform()
                curl.close()
        except pycurl.error:
            cls._check_status_code(pycurl.RESPONSE_CODE)

    @classmethod
    def _load_file_with_requests(
        cls,
        url,
        filename,
        filedir,
        real_file_size,
        display_loading,
        chunk_size=8 * 1024**2,
    ):
        with Session() as session:
            headers = {"Range": "bytes=%d-" % real_file_size}
            r = session.get(url, headers=headers, timeout=3, stream=True)
            try:
                cls._check_status_code(r.status_code)
            except RangeNotSatisfiableError:
                raise FileExistsError()
            total_size = float(r.headers["content-length"])
            thread_logger = ThreadLogger()
            with open(
                join(filedir, filename), "ab" if real_file_size else "wb"
            ) as file:
                try:
                    for i, chunk in enumerate(r.iter_content(chunk_size=chunk_size)):
                        cls._check_status_code(r.status_code)
                        if display_loading:
                            cls.log(
                                filename,
                                i * chunk_size + real_file_size,
                                total_size + real_file_size,
                            )
                        file.write(chunk)
                    thread_logger.info(filename, "Completed.")
                except RangeNotSatisfiableError:
                    return
                except Timeout:
                    raise RecoverableDownloadError
                except Exception:
                    raise NonRecoverableDownloadError
