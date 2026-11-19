"""Читання CSV і перетворення рядків на типізовані записи (без друку й без аналізу)."""

import csv
import math
from datetime import date
from pathlib import Path
from typing import TypedDict

from .errors import DataError

#: Обов'язкові стовпці CSV варіанта 2 («Спортивні тренування»).
REQUIRED_FIELDS = ("date", "kind", "duration", "distance", "pulse")


class Record(TypedDict):
    """Типізований запис про тренування (звичайний словник під час виконання)."""

    date: date
    kind: str
    duration: int
    distance: float
    pulse: int


def _check_header(fieldnames: list[str] | None) -> None:
    """Перевіряє, що заголовок містить рівно потрібні стовпці."""
    if not fieldnames:
        raise DataError("Файл порожній: відсутній заголовок CSV")
    missing = [name for name in REQUIRED_FIELDS if name not in fieldnames]
    extra = [name for name in fieldnames if name not in REQUIRED_FIELDS]
    if missing or extra:
        parts = []
        if missing:
            parts.append("відсутні стовпці: " + ", ".join(missing))
        if extra:
            parts.append("зайві стовпці: " + ", ".join(extra))
        raise DataError("Некоректний заголовок CSV (" + "; ".join(parts) + ")")


def _text(row: dict[str, str | None], row_number: int, field: str) -> str:
    """Повертає непорожнє текстове поле або DataError з номером рядка."""
    value = row[field]
    if value is None:
        raise DataError(f"Рядок {row_number}: відсутнє значення поля {field}")
    value = value.strip()
    if not value:
        raise DataError(f"Рядок {row_number}: поле {field} порожнє")
    return value


def _number(text: str, row_number: int, field: str, kind: type[int] | type[float]) -> float:
    """Перетворює текст на невід'ємне число; помилка містить рядок і поле."""
    try:
        # Перетворення виконується на межі входу, щоб analysis працював із числами.
        number = kind(text)
    except ValueError as error:
        expected = "цілим числом" if kind is int else "числом"
        raise DataError(f"Рядок {row_number}: поле {field} має бути {expected}") from error
    if isinstance(number, float) and not math.isfinite(number):
        raise DataError(f"Рядок {row_number}: поле {field} має бути скінченним числом")
    if number < 0:
        raise DataError(f"Рядок {row_number}: поле {field} не може бути від'ємним")
    return number


def parse_row(row: dict[str, str | None], row_number: int) -> Record:
    """Перетворює один словник DictReader на ``Record``.

    Args:
        row: рядок CSV; пропущені значення мають вигляд ``None``.
        row_number: номер рядка у файлі (для повідомлень про помилки).

    Raises:
        DataError: якщо значення відсутнє, порожнє, не число, від'ємне або дата хибна.
    """
    if None in row:
        raise DataError(f"Рядок {row_number}: забагато полів")
    raw_date = _text(row, row_number, "date")
    try:
        parsed_date = date.fromisoformat(raw_date)
    except ValueError as error:
        raise DataError(f"Рядок {row_number}: поле date має бути датою РРРР-ММ-ДД") from error
    return Record(
        date=parsed_date,
        kind=_text(row, row_number, "kind"),
        duration=int(_number(_text(row, row_number, "duration"), row_number, "duration", int)),
        distance=float(_number(_text(row, row_number, "distance"), row_number, "distance", float)),
        pulse=int(_number(_text(row, row_number, "pulse"), row_number, "pulse", int)),
    )


def load_records(path: Path) -> list[Record]:
    """Читає CSV-файл (UTF-8) і повертає типізовані записи.

    Правила: файл без заголовка — помилка; файл лише із заголовком — порожній список; ідентичні
    рядки не видаляються (кожен є окремим записом). Вхідний файл не змінюється.

    Raises:
        DataError: файл недоступний, заголовок або значення некоректні.
    """
    try:
        # newline="" передає керування роздільниками рядків модулю csv.
        with path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            _check_header(reader.fieldnames)
            records: list[Record] = []
            for row in reader:
                # line_num — фізичний номер рядка файла (враховує порожні рядки й multiline-поля).
                records.append(parse_row(row, reader.line_num))
            return records
    except (OSError, UnicodeDecodeError) as error:
        raise DataError(f"Не вдалося прочитати файл: {path}") from error
    except csv.Error as error:
        raise DataError(f"Пошкоджений CSV: {error}") from error
