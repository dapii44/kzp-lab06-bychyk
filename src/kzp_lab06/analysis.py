"""Обчислення над записами (без файлів і без форматування тексту)."""

from collections.abc import Sequence

from .loader import Record

#: Поріг відбору за умовою варіанта: тренування не коротші за 45 хв.
MIN_DURATION = 45

#: Числові поля, за якими можна обчислювати суми.
METRIC_FIELDS = ("duration", "distance", "pulse")


def select_long(records: Sequence[Record], min_duration: int = MIN_DURATION) -> list[Record]:
    """Відбирає тренування з ``duration >= min_duration`` у початковому порядку."""
    return [record for record in records if record["duration"] >= min_duration]


def unique_kinds(records: Sequence[Record]) -> set[str]:
    """Повертає множину унікальних видів тренувань (порядку не гарантує)."""
    return {record["kind"] for record in records}


def distance_by_kind(records: Sequence[Record]) -> dict[str, float]:
    """Обчислює сумарну дистанцію за видом; ключі впорядковано за алфавітом.

    Порожній список дає порожній словник: сума за видом без записів не створюється.
    """
    kinds = unique_kinds(records)
    # Сортування ключів робить звіт незалежним від порядку вхідних рядків.
    return {
        kind: sum(record["distance"] for record in records if record["kind"] == kind)
        for kind in sorted(kinds)
    }


def average_pulse(records: Sequence[Record]) -> float:
    """Повертає середній пульс; для порожнього списку — 0.0."""
    if not records:
        return 0.0
    return sum(record["pulse"] for record in records) / len(records)


def longest_workout(records: Sequence[Record]) -> Record | None:
    """Повертає найдовше тренування або ``None`` для порожнього списку.

    За однакової тривалості обирається раніша дата; якщо й дати збігаються — перший запис.
    """
    if not records:
        return None
    return max(records, key=lambda record: (record["duration"], -record["date"].toordinal()))


def make_summary(
    records: Sequence[Record],
    *metrics: str,
    min_duration: int = MIN_DURATION,
    **labels: str,
) -> dict[str, float]:
    """Обчислює суми вибраних метрик за відібраними записами.

    Args:
        records: усі записи.
        *metrics: назви числових полів (``duration``, ``distance``, ``pulse``).
        min_duration: поріг відбору (типове значення — незмінне число, без спільного стану).
        **labels: підписи результатів за назвою метрики, наприклад ``duration="Тривалість"``.

    Returns:
        Словник із ``"count"`` (кількість відібраних) і сумою кожної метрики; якщо всі записи
        відсіяно, визначені метрики мають значення 0.0.

    Raises:
        ValueError: якщо назва метрики невідома або підпис задано для незапитаної метрики.
    """
    for name in metrics:
        if name not in METRIC_FIELDS:
            raise ValueError(f"Невідома метрика: {name}")
    for name in labels:
        if name not in metrics:
            raise ValueError(f"Підпис задано для метрики, якої немає серед запитаних: {name}")
    selected = select_long(records, min_duration)
    result: dict[str, float] = {"count": float(len(selected))}
    for metric in metrics:
        result[labels.get(metric, metric)] = float(sum(record[metric] for record in selected))
    return result
