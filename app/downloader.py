import time
from dataclasses import dataclass
from typing import Callable

import requests


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)

DEFAULT_TIMEOUT = (10, 60)
DEFAULT_CHUNK_SIZE = 64_000


@dataclass
class DownloadResult:
    elapsed: float
    downloaded_bytes: int


class Downloader:
    def __init__(
        self,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        self.timeout = timeout
        self.chunk_size = chunk_size

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
        })

    def download(
        self,
        url: str,
        progress_callback: Callable[[float], None] | None = None,
    ) -> DownloadResult:
        downloaded_bytes = 0
        interval_bytes = 0

        start_time = time.perf_counter()
        interval_start = start_time

        with self.session.get(
            url,
            stream=True,
            timeout=self.timeout,
        ) as response:

            response.raise_for_status()

            for chunk in response.iter_content(
                chunk_size=self.chunk_size
            ):
                if not chunk:
                    continue

                chunk_bytes = len(chunk)

                downloaded_bytes += chunk_bytes
                interval_bytes += chunk_bytes

                current_time = time.perf_counter()
                interval_elapsed = current_time - interval_start

                if (
                    progress_callback is not None
                    and interval_elapsed >= 1
                ):
                    current_speed = interval_bytes / interval_elapsed

                    progress_callback(current_speed)

                    interval_bytes = 0
                    interval_start = current_time

        elapsed = time.perf_counter() - start_time

        if progress_callback is not None and interval_bytes > 0:
            interval_elapsed = time.perf_counter() - interval_start

            if interval_elapsed > 0:
                progress_callback(
                    interval_bytes / interval_elapsed
                )

        return DownloadResult(
            elapsed=elapsed,
            downloaded_bytes=downloaded_bytes,
        )

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()