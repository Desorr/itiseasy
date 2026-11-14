from dataclasses import dataclass

from app.downloader import DownloadResult


@dataclass
class DownloadStatistics:
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_bytes: int
    total_time: float
    average_time: float | None
    average_speed: float | None


def calculate_statistics(
    results: list[DownloadResult],
    total_requests: int,
) -> DownloadStatistics:

    successful_requests = len(results)
    failed_requests = total_requests - successful_requests

    total_bytes = sum(
        result.downloaded_bytes for result in results
    )

    total_time = sum(
        result.elapsed for result in results
    )

    average_time = (
        total_time / successful_requests
        if successful_requests
        else None
    )

    average_speed = (
        total_bytes / total_time
        if total_time > 0
        else None
    )

    return DownloadStatistics(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        total_bytes=total_bytes,
        total_time=total_time,
        average_time=average_time,
        average_speed=average_speed,
    )