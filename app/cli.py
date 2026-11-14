import argparse
import math
from urllib.parse import urlsplit

import requests

from app.downloader import Downloader, DownloadResult
from app.statistics import calculate_statistics


DEFAULT_COUNT = 10
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 60
DEFAULT_CHUNK_SIZE = 64

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_NO_SUCCESSFUL_DOWNLOADS = 2
EXIT_INTERRUPTED = 130

BYTES_IN_MB = 1_000_000
BYTES_IN_KB = 1_000


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Значение должно быть целым числом"
        )

    if number <= 0:
        raise argparse.ArgumentTypeError(
            "Значение должно быть больше нуля"
        )

    return number


def positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Значение должно быть числом"
        )

    if not math.isfinite(number):
        raise argparse.ArgumentTypeError(
            "Значение должно быть конечным числом"
        )

    if number <= 0:
        raise argparse.ArgumentTypeError(
            "Значение должно быть больше нуля"
        )

    return number


def validate_url(value: str) -> str:
    try:
        parsed = urlsplit(value)

        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
        ):
            raise ValueError

        parsed.port

    except ValueError:
        raise argparse.ArgumentTypeError(
            "Укажите корректный HTTP или HTTPS URL"
        )

    return value


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="HTTP Download Speed Test"
    )

    parser.add_argument(
        "url",
        type=validate_url,
        help="URL для скачивания",
    )

    parser.add_argument(
        "--count",
        type=positive_int,
        default=DEFAULT_COUNT,
        help=f"Количество запросов (по умолчанию: {DEFAULT_COUNT})",
    )

    parser.add_argument(
        "--connect-timeout",
        type=positive_float,
        default=DEFAULT_CONNECT_TIMEOUT,
        help="Таймаут подключения в секундах",
    )

    parser.add_argument(
        "--read-timeout",
        type=positive_float,
        default=DEFAULT_READ_TIMEOUT,
        help="Таймаут чтения в секундах",
    )

    parser.add_argument(
        "--chunk-size",
        type=positive_int,
        default=DEFAULT_CHUNK_SIZE,
        help="Размер блока скачивания в KB",
    )

    return parser


def print_statistics(statistics):
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 50)

    print(
        f"Успешных запросов: "
        f"{statistics.successful_requests}/{statistics.total_requests}"
    )

    print(f"Ошибок: {statistics.failed_requests}")

    print(
        f"Общий объём: "
        f"{statistics.total_bytes / BYTES_IN_MB:.2f} MB"
    )

    print(f"Общее время: {statistics.total_time:.3f} сек.")

    if statistics.average_time is not None:
        print(
            f"Среднее время запроса: "
            f"{statistics.average_time:.3f} сек."
        )

    if statistics.average_speed is not None:
        speed = statistics.average_speed / BYTES_IN_MB

        print(f"Средняя скорость: {speed:.4f} MB/s")

    print("=" * 50)


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    results: list[DownloadResult] = []

    print(f"URL: {args.url}")
    print(f"Количество запросов: {args.count}")
    print("-" * 50)

    try:
        with Downloader(
            timeout=(
                args.connect_timeout,
                args.read_timeout,
            ),
            chunk_size=args.chunk_size * BYTES_IN_KB,
        ) as downloader:

            for i in range(1, args.count + 1):
                print(f"\nЗапрос {i}/{args.count}: скачивание...")

                def show_progress(speed_bytes: float):
                    speed_mb = speed_bytes / BYTES_IN_MB

                    print(
                        f"  Текущая скорость: {speed_mb:.4f} MB/s"
                    )

                try:
                    result = downloader.download(
                        args.url,
                        progress_callback=show_progress,
                    )

                    results.append(result)

                    size_mb = result.downloaded_bytes / BYTES_IN_MB

                    print(
                        f"  Завершено: {result.elapsed:.3f} сек. | "
                        f"{size_mb:.2f} MB"
                    )

                except requests.RequestException as error:
                    print(f"  Ошибка: {error}")

    except KeyboardInterrupt:
        print("\nВыполнение прервано пользователем.")
        return EXIT_INTERRUPTED

    statistics = calculate_statistics(
        results=results,
        total_requests=args.count,
    )

    print_statistics(statistics)

    if statistics.successful_requests == 0:
        print("\nРезультат: не удалось выполнить ни одного запроса.")
        return EXIT_NO_SUCCESSFUL_DOWNLOADS

    if statistics.failed_requests > 0:
        print("\nРезультат: выполнение завершено с ошибками.")
        return EXIT_ERROR

    print("\nРезультат: все запросы успешно выполнены.")
    return EXIT_SUCCESS