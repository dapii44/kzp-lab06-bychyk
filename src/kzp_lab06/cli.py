"""Командний рядок: межа, де помилки стають повідомленнями й кодами завершення."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .analysis import MIN_DURATION
from .errors import DataError
from .loader import load_records
from .reporting import format_report, write_report

#: Код успішного завершення.
EXIT_OK = 0
#: Код неочікуваної помилки програми.
EXIT_UNEXPECTED = 1
#: Код очікуваної помилки даних (аргументи argparse також завершуються кодом 2).
EXIT_DATA_ERROR = 2


def _reconfigure_streams() -> None:
    """Задає UTF-8 для stdout і stderr: консоль Windows може мати інше кодування."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            # Потік без reconfigure (наприклад, підмінений у тесті) лишається як є.
            pass


def build_parser() -> argparse.ArgumentParser:
    """Створює парсер аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        prog="kzp-lab06", description="Звіт про спортивні тренування з CSV."
    )
    parser.add_argument("input_csv", type=Path, help="вхідний CSV (не змінюється)")
    parser.add_argument("output_report", type=Path, help="файл звіту (створюється або замінюється)")
    parser.add_argument(
        "--min-duration",
        type=int,
        default=MIN_DURATION,
        help=f"поріг відбору, хв (типово {MIN_DURATION})",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Виконує програму й повертає код завершення.

    Returns:
        0 — успіх; 2 — очікувана помилка даних (повідомлення в stderr); 1 — неочікувана помилка.
    """
    args = build_parser().parse_args(argv)
    _reconfigure_streams()
    try:
        records = load_records(args.input_csv)
        write_report(args.output_report, format_report(records, args.min_duration))
    except DataError as error:
        print(f"Помилка даних: {error}", file=sys.stderr)
        return EXIT_DATA_ERROR
    except Exception as error:  # межа CLI: неочікувану помилку не маскуємо
        print(f"Неочікувана помилка: {error!r}", file=sys.stderr)
        return EXIT_UNEXPECTED
    print(f"Звіт записано: {args.output_report}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
