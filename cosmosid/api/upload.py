"""Interactions with CosmosID's and S3's APIs regarding file uploads to S3."""

import base64
import hashlib
import logging
import os
import sys
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util import Retry  # type: ignore
except Exception:  # pragma: no cover
    Retry = None  # fallback – session retries disabled

from cosmosid.api import urls
from cosmosid.helpers.exceptions import UploadException
from cosmosid.utils import LOCK, requests_retry_session

LOGGER = logging.getLogger(__name__)
KB = 1024
MB = 1024 * KB
DEFAULT_PART_SIZE_MB = 6  # baseline default; overridden only via function parameters
PART_SIZE = DEFAULT_PART_SIZE_MB * MB
SMALL_FILE_THRESHOLD = PART_SIZE * 1
MAX_PART_RETRIES = 5
PART_BACKOFF_BASE = 1.5
MAX_CONCURRENCY_DEFAULT = 5
RESET_FALLBACK_THRESHOLD = 5  # after this many connection resets fallback to sequential

TRUNCATION_SUFFIX = "...<truncated>"


class ProgressReporter:
    """Stateful progress reporter (callable) tracking speed and ETA.

    Replaces the _progress_reporter closure while staying API compatible
    (instances are callable with delta bytes uploaded).
    """

    __slots__ = ("file_name", "file_size", "_uploaded", "_start")

    def __init__(self, file_name: str, file_size: int):
        self.file_name = file_name
        self.file_size = file_size
        self._uploaded = 0
        self._start = time.time()

    @staticmethod
    def _human_rate(bps: float) -> str:
        if bps <= 0:
            return "0 B/s"
        units = ["B/s", "KB/s", "MB/s", "GB/s"]
        idx = 0
        while bps >= 1024 and idx < len(units) - 1:
            bps /= 1024.0
            idx += 1
        if idx == 0:
            return f"{int(bps)} {units[idx]}"
        return f"{bps:.2f} {units[idx]}"

    def __call__(self, delta: int):  # pragma: no cover - simple
        self._uploaded += delta
        now = time.time()
        elapsed = max(now - self._start, 1e-6)
        speed = self._uploaded / elapsed
        remaining = max(self.file_size - self._uploaded, 0)
        eta = remaining / speed if speed > 0 else 0
        if eta >= 3600:
            eta_str = f"{int(eta // 3600)}h{int((eta % 3600) // 60)}m"
        elif eta >= 60:
            eta_str = f"{int(eta // 60)}m{int(eta % 60)}s"
        else:
            eta_str = f"{int(eta)}s"
        status = f"Uploading {self.file_name} | {self._human_rate(speed)} | ETA {eta_str}"
        try:
            from cosmosid.utils import progress as progress_fn  # local import

            progress_fn(self._uploaded, self.file_size, status=status)
        except Exception:
            pass


class _MultipartUploader:
    """Stateful multipart uploader with adaptive fallback to sequential mode.

    api_session handles CosmosID API calls.
    Each worker thread obtains its own session for S3 PUTs via _get_upload_session().
    """

    def __init__(
        self,
        session,
        client,
        bucket,
        upload_key,
        filename,
        file_size,
        concurrency,
        report,
        part_size,
    ):
        self.api_session = session
        self.client = client
        self.bucket = bucket
        self.upload_key = upload_key
        self.filename = filename
        self.file_size = file_size
        self.concurrency = concurrency
        self.report = report
        self.upload_id = None
        self.parts = []
        self.resets = 0
        self.fallback_triggered = False
        self.lock = LOCK
        self.part_size = part_size

    def init(self):
        payload = {"Bucket": self.bucket, "Key": self.upload_key}
        resp = self.api_session.put(
            self.client.burl,
            json=payload,
            headers=self.client.header,
            timeout=30,
        )
        try:
            body = resp.text if isinstance(getattr(resp, "text", None), str) else None
            if body and len(body) > 2000:
                body = body[:2000] + TRUNCATION_SUFFIX
            LOGGER.debug(
                json.dumps(
                    {
                        "event": "multipart_init",
                        "method": "PUT",
                        "url": self.client.burl,
                        "payload": payload,
                        "status": resp.status_code,
                        "body": body,
                    },
                    default=str,
                )
            )
        except Exception:
            pass
        if resp.status_code != requests.codes.ok:
            raise UploadException("Failed to create multipart upload.")
        data = resp.json() or {}
        self.upload_id = data.get("UploadId") or data.get("UploadID")
        if not self.upload_id:
            raise UploadException("UploadId missing from multipart init response.")

    def presign_part(self, part_number, md5_b64):
        payload = {
            "Bucket": self.bucket,
            "Key": self.upload_key,
            "PartNumber": part_number,
            "UploadId": self.upload_id,
            "ContentMD5": md5_b64,
        }
        resp = self.api_session.get(
            self.client.burl,
            json=payload,
            headers=self.client.header,
            timeout=30,
        )
        try:
            body = resp.text if isinstance(getattr(resp, "text", None), str) else None
            if body and len(body) > 2000:
                body = body[:2000] + TRUNCATION_SUFFIX
            LOGGER.debug(
                json.dumps(
                    {
                        "event": "presign_part",
                        "method": "GET",
                        "url": self.client.burl,
                        "part_number": part_number,
                        "payload": payload,
                        "status": resp.status_code,
                        "body": body,
                    },
                    default=str,
                )
            )
        except Exception:  # pragma: no cover
            pass
        if resp.status_code != requests.codes.ok:
            raise UploadException(f"Presign failed part {part_number} HTTP {resp.status_code}")
        return resp.json()

    def put_part(self, url, part_number, data_bytes, md5_b64):
        size = len(data_bytes)
        up_session = _get_upload_session()
        start = time.time()
        headers = {
            "Content-MD5": md5_b64,
            "Content-Length": str(size),
        }  # intentionally no Content-Type
        LOGGER.debug(
            json.dumps(
                {
                    "event": "part_put_start",
                    "part_number": part_number,
                    "url": url,
                    "size": size,
                    "streaming": False,
                },
                default=str,
            )
        )
        try:
            resp = up_session.put(url, data=data_bytes, headers=headers, timeout=(30, 600))
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug(
                json.dumps(
                    {
                        "event": "part_put_error",
                        "part_number": part_number,
                        "error": str(exc),
                        "elapsed": round(time.time() - start, 3),
                    },
                    default=str,
                )
            )
            raise
        elapsed = time.time() - start
        if resp.status_code in (200, 201):
            self.report(size)
            etag = resp.headers.get("ETag")
            if not etag:
                LOGGER.debug(
                    json.dumps(
                        {
                            "event": "part_put_missing_etag",
                            "part_number": part_number,
                            "status": resp.status_code,
                            "elapsed": round(elapsed, 3),
                        },
                        default=str,
                    )
                )
                raise UploadException(f"Missing ETag for part {part_number}")
            with self.lock:
                self.parts.append({"ETag": etag.strip('"'), "PartNumber": part_number})
            LOGGER.debug(
                json.dumps(
                    {
                        "event": "part_put_ok",
                        "part_number": part_number,
                        "status": resp.status_code,
                        "etag": etag,
                        "elapsed": round(elapsed, 3),
                    },
                    default=str,
                )
            )
            return
        body_sample = resp.text[:500] if hasattr(resp, "text") else None
        try:
            LOGGER.debug(
                json.dumps(
                    {
                        "event": "part_put_failed",
                        "part_number": part_number,
                        "status": resp.status_code,
                        "elapsed": round(elapsed, 3),
                        "headers": dict(resp.headers),
                        "body": body_sample,
                    },
                    default=str,
                )
            )
        except Exception:
            pass
        raise UploadException(f"Part {part_number} failed HTTP {resp.status_code}")

    def upload_part(self, part_number, data_bytes):
        md5_b64 = base64.b64encode(hashlib.md5(data_bytes).digest()).decode("ascii")
        attempt = 0
        last_exc = None
        reset_fallback_threshold = int(
            os.getenv(
                "COSMOSID_UPLOAD_RESET_FALLBACK_THRESHOLD",
                str(RESET_FALLBACK_THRESHOLD),
            )
        )
        while attempt < MAX_PART_RETRIES:
            try:
                url = self.presign_part(part_number, md5_b64)
                self.put_part(url, part_number, data_bytes, md5_b64)
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                attempt += 1
                if "Connection reset" in str(exc):
                    with self.lock:
                        self.resets += 1
                        if (
                            self.resets >= reset_fallback_threshold
                            and self.concurrency > 1
                            and not self.fallback_triggered
                        ):
                            self.fallback_triggered = True
                            LOGGER.warning(
                                "Connection resets reached %d (threshold %d). Switching to sequential for remaining parts.",
                                self.resets,
                                reset_fallback_threshold,
                            )
                if attempt >= MAX_PART_RETRIES:
                    break
                backoff = PART_BACKOFF_BASE**attempt
                LOGGER.warning(
                    "Retry part %s attempt %s/%s after error: %s (sleep %.2fs)",
                    part_number,
                    attempt,
                    MAX_PART_RETRIES,
                    exc,
                    backoff,
                )
                time.sleep(backoff)
        raise UploadException(f"Part {part_number} failed after retries: {last_exc}")

    def upload_all_parts(self):
        part_number = 1
        remaining_offset = None
        with (
            open(self.filename, "rb") as fh,
            ThreadPoolExecutor(max_workers=self.concurrency) as pool,
        ):
            futures = []
            while True:
                chunk = fh.read(self.part_size)
                if not chunk:
                    break
                futures.append(pool.submit(self.upload_part, part_number, chunk))
                part_number += 1
                if self.fallback_triggered:
                    remaining_offset = fh.tell()
                    break
            for fut in as_completed(futures):
                fut.result()
        if self.fallback_triggered and remaining_offset is not None:
            with open(self.filename, "rb") as fh_seq:
                fh_seq.seek(remaining_offset)
                while True:
                    chunk = fh_seq.read(self.part_size)
                    if not chunk:
                        break
                    self.upload_part(part_number, chunk)
                    part_number += 1

    def complete(self):
        payload = {
            "Bucket": self.bucket,
            "Key": self.upload_key,
            "UploadId": self.upload_id,
            "MultipartUpload": {"Parts": sorted(self.parts, key=lambda p: p["PartNumber"])},
        }
        finish = self.api_session.post(self.client.burl, json=payload, headers=self.client.header, timeout=120)
        try:
            body = finish.text if isinstance(getattr(finish, "text", None), str) else None
            if body and len(body) > 2000:
                body = body[:2000] + TRUNCATION_SUFFIX
            LOGGER.debug(
                json.dumps(
                    {
                        "event": "multipart_complete",
                        "method": "POST",
                        "url": self.client.burl,
                        "payload": payload,
                        "status": finish.status_code,
                        "body": body,
                    },
                    default=str,
                )
            )
        except Exception:
            pass
        if finish.status_code != requests.codes.ok:
            raise UploadException("Failed to complete multipart upload.")

    def abort(self):
        if not self.upload_id:
            return
        try:
            payload = {
                "Bucket": self.bucket,
                "Key": self.upload_key,
                "UploadId": self.upload_id,
            }
            resp = self.api_session.delete(
                self.client.burl,
                json=payload,
                headers=self.client.header,
                timeout=30,
            )
            try:
                body = getattr(resp, "text", None)
                if isinstance(body, str) and len(body) > 2000:
                    body = body[:2000] + TRUNCATION_SUFFIX
                LOGGER.debug(
                    json.dumps(
                        {
                            "event": "multipart_abort",
                            "method": "DELETE",
                            "url": self.client.burl,
                            "payload": payload,
                            "status": getattr(resp, "status_code", None),
                            "body": body,
                        },
                        default=str,
                    )
                )
            except Exception:  # pragma: no cover
                pass
        except Exception:  # pragma: no cover
            pass

    def run(self):
        try:
            self.init()
            self.upload_all_parts()
            self.complete()
            sys.stdout.write("\n")
            return self.upload_key
        except Exception:
            self.abort()
            raise


class Uploader:
    """High-level uploader orchestrating single or multipart uploads.

    Usage:
      uploader = Uploader(file_path=..., file_type=..., parent_id=..., api_key=..., base_url=...)
      upload_key = uploader.run()
    """

    def __init__(
        self,
        *,
        file_path,
        file_type,
        parent_id,
        api_key,
        base_url,
        concurrency=None,
        part_size_mb=None,
        logger: logging.Logger = LOGGER,
    ):
        # Inputs / config
        self.file_path = file_path
        self.file_type = file_type
        self.parent_id = parent_id
        self.api_key = api_key
        self.base_url = base_url
        self.concurrency = concurrency or int(os.getenv("COSMOSID_UPLOAD_CONCURRENCY", str(MAX_CONCURRENCY_DEFAULT)))
        self._logger = logger
        # Derived / runtime state
        self.client = self.create_client(base_url, api_key)
        self.session = self._build_session(self.concurrency)
        self.bucket = None
        self.upload_key = None
        self.size = None
        self.report = None
        # Part size (at least 4MB to satisfy S3 multi-part minimum)
        if part_size_mb is not None and part_size_mb >= 4:
            self.part_size = part_size_mb * MB
        else:
            self.part_size = PART_SIZE

    def _init_file(self):
        size = os.path.getsize(self.file_path)
        payload = {
            "file_name": os.path.basename(self.file_path),
            "file_type": self.file_type,
            "file_size": size,
            "folder_id": self.parent_id,
        }
        try:
            resp = self.session.put(
                self.client.init_url,
                json=payload,
                headers=self.client.header,
                timeout=60,
            )
        except requests.RequestException as exc:  # pragma: no cover
            self._logger.debug(
                json.dumps(
                    {
                        "event": "upload_init_error",
                        "method": "PUT",
                        "url": self.client.init_url,
                        "payload": payload,
                        "error": str(exc),
                    },
                    default=str,
                )
            )
            raise UploadException(f"Init upload network error: {exc}") from exc
        body = getattr(resp, "text", None)
        if isinstance(body, str) and len(body) > 2000:
            body = body[:2000] + TRUNCATION_SUFFIX
        self._logger.debug(
            json.dumps(
                {
                    "event": "upload_init",
                    "method": "PUT",
                    "url": self.client.init_url,
                    "payload": payload,
                    "status": resp.status_code,
                    "body": body,
                },
                default=str,
            )
        )
        if resp.status_code == 403:
            raise UploadException("Authentication failed (403)")
        if resp.status_code == 404:
            raise UploadException("Parent folder not found (404)")
        if resp.status_code == 405:
            raise UploadException(
                "Init upload failed (405 Method Not Allowed) - ensure endpoint /upload_init supports PUT and CLI base_url is correct"
            )
        if resp.status_code not in (200, 201):
            raise UploadException(f"Init upload failed HTTP {resp.status_code}")
        try:
            js = resp.json() or {}
        except ValueError:
            raise UploadException("Init upload returned non-JSON response")
        bucket = js.get("upload_source") or js.get("bucket") or js.get("Bucket")
        upload_key = js.get("upload_key") or js.get("key") or js.get("Key")
        if not bucket or not upload_key:
            raise UploadException(f"Init response missing upload_source/upload_key fields: {js}")
        self.bucket, self.upload_key, self.size = bucket, upload_key, size

    def _select_strategy(self):
        if self.size is None:
            raise UploadException("File size unknown before selecting strategy")
        if self.size <= SMALL_FILE_THRESHOLD:
            return SmallFileUploadStrategy(self)
        return MultipartUploadStrategy(self)

    @staticmethod
    def _build_session(concurrency: int) -> requests.Session:
        """Create a requests.Session with retry adapter sized to concurrency.

        Retries only idempotent metadata operations (GET/POST) and allows part PUT
        retries to be handled explicitly in code.
        """
        session = requests.Session()
        if Retry is not None:
            try:
                retry_cfg = Retry(
                    total=3,
                    connect=3,
                    read=2,
                    backoff_factor=0.3,  # type: ignore[arg-type]
                    status_forcelist=[500, 502, 503, 504],
                    allowed_methods=["GET", "PUT", "POST"],
                )
                adapter = HTTPAdapter(
                    max_retries=retry_cfg,
                    pool_connections=concurrency * 2,
                    pool_maxsize=concurrency * 2,
                )
                session.mount("http://", adapter)
                session.mount("https://", adapter)
            except Exception:  # pragma: no cover
                pass
        return session

    @staticmethod
    def create_client(base_url, api_key):
        """Lightweight struct with upload endpoint URLs and headers."""

        class _UploadClient:
            def __init__(self, base_url, api_key):
                if base_url and not base_url.startswith("http"):
                    base_url = f"https://{base_url}"
                self.base_url = base_url.rstrip("/") if base_url else "https://app.cosmosid.com"
                self.header = {"X-API-Key": api_key} if api_key else {}
                self.init_url = self.base_url + urls.UPLOAD_INIT_URL
                self.burl = self.base_url + urls.UPLOAD_BFILE_URL
                self.surl = self.base_url + urls.UPLOAD_SFILE_URL

        return _UploadClient(base_url, api_key)

    def run(self):
        self._init_file()
        assert self.size is not None
        self.report = ProgressReporter(os.path.basename(self.file_path), self.size)
        strategy = self._select_strategy()
        return strategy.run()


class _BaseUploadStrategy:
    """Common base for upload strategies."""

    def __init__(self, uploader: "Uploader"):
        self.uploader = uploader

    def run(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class SmallFileUploadStrategy(_BaseUploadStrategy):
    """Handles single part file uploads."""

    def run(self) -> str:
        u = self.uploader
        if u.bucket is None or u.upload_key is None or u.size is None:
            raise UploadException("Uploader not initialized before small upload")
        if u.report is None:
            u.report = ProgressReporter(os.path.basename(u.file_path), u.size)

        md5 = hashlib.md5()
        with open(u.file_path, "rb") as fh:
            data = fh.read()
            md5.update(data)
        md5_b64 = base64.b64encode(md5.digest()).decode("ascii")

        presign_payload = {
            "Bucket": u.bucket,
            "Key": u.upload_key,
            "ContentMD5": md5_b64,
        }
        presign_resp = u.session.get(u.client.surl, json=presign_payload, headers=u.client.header, timeout=60)
        body = presign_resp.text
        if isinstance(body, str) and len(body) > 2000:
            body = body[:2000] + TRUNCATION_SUFFIX
        u._logger.debug(
            json.dumps(
                {
                    "event": "presign_single_part",
                    "method": "GET",
                    "url": u.client.surl,
                    "payload": presign_payload,
                    "status": presign_resp.status_code,
                    "body": body,
                },
                default=str,
            )
        )
        if presign_resp.status_code != 200:
            raise UploadException(f"Presign single-part failed HTTP {presign_resp.status_code}")
        url = presign_resp.json()

        size = len(data)
        put_session = _get_upload_session()
        headers = {"Content-MD5": md5_b64, "Content-Length": str(size)}
        u._logger.debug(json.dumps({"event": "single_put_start", "url": url, "size": size}, default=str))
        resp = put_session.put(url, data=data, headers=headers, timeout=(30, 600))
        if resp.status_code not in (200, 201):
            body_fail = resp.text[:500] if hasattr(resp, "text") else None
            u._logger.debug(
                json.dumps(
                    {
                        "event": "single_put_failed",
                        "url": url,
                        "status": resp.status_code,
                        "body": body_fail,
                    },
                    default=str,
                )
            )
            raise UploadException(f"Single-part upload failed HTTP {resp.status_code}")
        u.report(size)
        sys.stdout.write("\n")
        return u.upload_key  # type: ignore[return-value]


class MultipartUploadStrategy(_BaseUploadStrategy):
    """Handles multipart uploads."""

    def run(self) -> str:
        u = self.uploader
        mp = _MultipartUploader(
            session=u.session,
            client=u.client,
            bucket=u.bucket,
            upload_key=u.upload_key,
            filename=u.file_path,
            file_size=u.size,
            concurrency=u.concurrency,
            report=u.report,
            part_size=u.part_size,
        )
        key = mp.run()
        if not isinstance(key, str):  # pragma: no cover - safety
            raise UploadException("Multipart upload did not return key")
        return key


# Thread-local session for S3 PUT operations
_S3_THREAD_LOCAL = threading.local()


def _get_upload_session() -> requests.Session:  # pragma: no cover - simple helper
    session = getattr(_S3_THREAD_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        try:
            adapter = HTTPAdapter(pool_connections=4, pool_maxsize=4)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        except Exception:
            pass
        _S3_THREAD_LOCAL.session = session
    return session


def upload_file(*, file, file_type, parent_id=None, api_key, base_url, concurrency=None, part_size_mb=None):
    uploader = Uploader(
        file_path=file,
        file_type=file_type,
        parent_id=parent_id,
        api_key=api_key,
        base_url=base_url,
        concurrency=concurrency,
        part_size_mb=part_size_mb,
    )
    return uploader.run()


def upload_and_save(*, files, parent_id=None, file_type, base_url, api_key, concurrency=None, part_size_mb=None):
    if not files:
        raise UploadException("No files provided")
    first = upload_file(
        file=files[0],
        file_type=file_type,
        parent_id=parent_id,
        api_key=api_key,
        base_url=base_url,
        concurrency=concurrency,
        part_size_mb=part_size_mb,
    )
    return {"id": first} if first else None


def pricing(*, data, base_url, api_key):
    """Return pricing info for provided samples payload.

    Parameters:
      data: list of sample pricing request dicts
      base_url: API base URL
      api_key: API key for auth
    """
    if base_url and not base_url.startswith("http"):
        base_url = f"https://{base_url}"
    base_url = base_url.rstrip("/") if base_url else "https://app.cosmosid.com"
    hdr = {"X-API-Key": api_key} if api_key else {}
    url = base_url + urls.SAMPLES_PRICING_URL
    resp = requests_retry_session().post(url=url, json={"data": data}, headers=hdr)
    if resp.status_code != 200:
        raise UploadException(f"Pricing request failed HTTP {resp.status_code}")
    js = resp.json()
    # Expecting list; if API returns object wrap for backward compatibility
    if isinstance(js, dict):
        return [js]
    return js
