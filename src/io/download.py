from __future__ import annotations
import logging
from pathlib import Path
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _get(url: str, timeout_s: int) -> requests.Response:
    """
    Perform HTTP GET request with automatic retry and exponential backoff.

    Retries up to 3 times on failure.
    Backoff grows exponentially between 1s and 8s.
    """
    r = requests.get(url, timeout=timeout_s)

    # Raise HTTPError for non-2xx responses
    r.raise_for_status()
    return r

def download_file(url: str, dest: Path, timeout_s: int = 20) -> Path:
    """
    Download a file from `url` into `dest` (creates parent dirs).
    """

    # Ensure destination directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("Downloading %s -> %s", url, dest)
    # HTTP request with retry protection
    r = _get(url, timeout_s)
    # Write binary content to disk
    dest.write_bytes(r.content)
    return dest