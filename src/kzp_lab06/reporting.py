"""Формування тексту звіту й запис його у файл (без читання CSV)."""

from collections.abc import Sequence
from pathlib import Path

from .analysis import (
    MIN_DURATION,
    average_pulse,
    distance_by_kind,
    longest_workout,
    make_summary,
    select_long,
    unique_kinds,
)
from .errors import DataError
from .loader import Record


def format_report(records: Sequence[Record], min_duration: int = MIN_DURATION) -> str:
    """Формує детермінований текстовий звіт за записами.

    Порядок рядків фіксований, види впорядковано за алфавітом, числа форматуються явно
    (крапка як десятковий роздільник), тому результат не залежить від порядку вхідних рядків.
    """
    selected = select_long(records, min_duration)
    totals = make_summary(
        records,
        "duration",
        "distance",
        min_duration=min_duration,
        duration="Тривалість, хв",
        distance="Дистанція, км",
    )
    lines = [
        "Звіт про тренування",
        f"Записів у файлі: {len(records)}",
        f"Відібрано (тривалість >= {min_duration} хв): {len(selected)}",
        "Види тренувань: " + ("; ".join(sorted(unique_kinds(records))) or "немає"),
        f"Сума за відібраними: Тривалість, хв = {totals['Тривалість, хв']:.2f}; "
        f"Дистанція, км = {totals['Дистанція, км']:.2f}",
        "Дистанція за видом (відібрані):",
    ]
    by_kind = distance_by_kind(selected)
    lines += [f"  {kind}: {distance:.2f} км" for kind, distance in by_kind.items()]
    if not by_kind:
        lines.append("  немає записів")
    lines.append(f"Середній пульс: {average_pulse(records):.2f}")
    longest = longest_workout(records)
    if longest is None:
        lines.append("Найдовше тренування: немає даних")
    else:
        lines.append(
            f"Найдовше тренування: {longest['date'].isoformat()}, {longest['kind']}, "
            f"{longest['duration']} хв, {longest['distance']:.2f} км, пульс {longest['pulse']}"
        )
    return "\n".join(lines) + "\n"


def write_report(path: Path, text: str) -> None:
    """Записує звіт у файл UTF-8 (``\\n`` на всіх ОС), створюючи каталог за потреби.

    Raises:
        DataError: якщо файл неможливо записати.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # with гарантує закриття файла навіть у разі помилки запису.
        with path.open("w", encoding="utf-8", newline="\n") as target:
            target.write(text)
    except OSError as error:
        raise DataError(f"Не вдалося записати звіт: {path}") from error
