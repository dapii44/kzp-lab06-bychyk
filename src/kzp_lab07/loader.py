"""Читання CSV і перетворення рядків на об'єкти ``Training`` (без друку й без аналізу)."""

import csv
import datetime as dt
from pathlib import Path

from .errors import DataError
from .models import Cycling, Running, Training

#: Обов'язкові стовпці CSV (формат не змінився з лабораторної № 6).
REQUIRED_FIELDS = ("date", "kind", "duration", "distance", "pulse")

#: Види, навантаження яких оцінюється за дистанцією (підтип ``Cycling``); решта — ``Running``.
DISTANCE_KINDS = frozenset({"велосипед"})


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


def _convert(text: str, row_number: int, field: str, kind: type[int] | type[float]):
    """Перетворює текст на число; помилка містить рядок і поле."""
    try:
        return kind(text)
    except ValueError as error:
        expected = "цілим числом" if kind is int else "числом"
        raise DataError(f"Рядок {row_number}: поле {field} має бути {expected}") from error


def build_training(row: dict[str, str | None], row_number: int) -> Training:
    """Перетворює один словник ``DictReader`` на об'єкт відповідного підтипу.

    Фабрика використовує значення ``kind`` лише тут, на межі завантаження; далі код працює зі
    спільним типом. Правила значень перевіряють властивості моделі.

    Raises:
        DataError: якщо значення відсутнє, не є числом/датою або порушує правила моделі.
    """
    if None in row:
        raise DataError(f"Рядок {row_number}: забагато полів")
    raw_date = _text(row, row_number, "date")
    try:
        parsed_date = dt.date.fromisoformat(raw_date)
    except ValueError as error:
        raise DataError(f"Рядок {row_number}: поле date має бути датою РРРР-ММ-ДД") from error
    kind = _text(row, row_number, "kind")
    duration = _convert(_text(row, row_number, "duration"), row_number, "duration", int)
    distance = _convert(_text(row, row_number, "distance"), row_number, "distance", float)
    pulse = _convert(_text(row, row_number, "pulse"), row_number, "pulse", int)
    subtype = Cycling if kind.casefold() in DISTANCE_KINDS else Running
    try:
        return subtype(parsed_date, kind, duration, distance, pulse)
    except (TypeError, ValueError) as error:
        raise DataError(f"Рядок {row_number}: {error}") from error


def load_trainings(path: Path) -> list[Training]:
    """Читає CSV-файл (UTF-8) і повертає об'єкти тренувань у порядку файла.

    Правила збігаються з лабораторною № 6: файл без заголовка — помилка; лише заголовок — порожній
    список; ідентичні рядки не видаляються. Вхідний файл не змінюється.

    Raises:
        DataError: файл недоступний, заголовок або значення некоректні.
    """
    try:
        # newline="" передає керування роздільниками рядків модулю csv.
        with path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            _check_header(reader.fieldnames)
            trainings: list[Training] = []
            for row in reader:
                # line_num — фізичний номер рядка (враховує порожні рядки й multiline-поля).
                trainings.append(build_training(row, reader.line_num))
            return trainings
    except (OSError, UnicodeDecodeError) as error:
        raise DataError(f"Не вдалося прочитати файл: {path}") from error
    except csv.Error as error:
        raise DataError(f"Пошкоджений CSV: {error}") from error
