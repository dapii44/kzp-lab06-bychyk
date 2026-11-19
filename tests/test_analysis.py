"""Тести обчислень над записами."""

from datetime import date

import pytest

from kzp_lab06.analysis import (
    average_pulse,
    distance_by_kind,
    longest_workout,
    make_summary,
    select_long,
    unique_kinds,
)
from kzp_lab06.loader import Record


def rec(day: int, kind: str, duration: int, distance: float, pulse: int) -> Record:
    """Створює запис для тестів."""
    return Record(
        date=date(2026, 9, day), kind=kind, duration=duration, distance=distance, pulse=pulse
    )


RECORDS = [
    rec(1, "Біг", 45, 7.5, 148),
    rec(2, "Велосипед", 90, 28.4, 132),
    rec(3, "Плавання", 30, 1.2, 125),
    rec(4, "Силове, зал", 60, 0.0, 118),
    rec(5, "Біг", 50, 8.1, 152),
    rec(6, "Ходьба", 44, 3.4, 102),
]


def test_select_long_includes_boundary_and_excludes_shorter() -> None:
    """45 хв входить, 44 хв — ні; порядок початковий."""
    selected = select_long(RECORDS)

    assert [r["date"].day for r in selected] == [1, 2, 4, 5]
    assert all(r["duration"] >= 45 for r in selected)


def test_select_long_custom_threshold_and_empty() -> None:
    """Власний поріг працює; порожній вхід дає порожній результат."""
    assert [r["date"].day for r in select_long(RECORDS, 90)] == [2]
    assert select_long([]) == []
    assert select_long(RECORDS, 1000) == []


def test_unique_kinds_removes_duplicates() -> None:
    """Множина видів не містить повторів («Біг» двічі)."""
    kinds = unique_kinds(RECORDS)

    assert isinstance(kinds, set)
    assert kinds == {"Біг", "Велосипед", "Плавання", "Силове, зал", "Ходьба"}
    assert unique_kinds([]) == set()


def test_distance_by_kind_sums_and_sorts_keys() -> None:
    """Суми за видом, ключі за алфавітом незалежно від порядку входу."""
    totals = distance_by_kind(RECORDS)

    assert list(totals) == sorted(totals)
    assert totals["Біг"] == pytest.approx(15.6)
    assert totals["Велосипед"] == pytest.approx(28.4)
    assert distance_by_kind(list(reversed(RECORDS))) == totals


def test_distance_by_kind_empty_is_empty_dict() -> None:
    """Порожній список — порожній словник."""
    assert distance_by_kind([]) == {}


def test_average_pulse() -> None:
    """Середній пульс і значення для порожнього списку."""
    assert average_pulse(RECORDS) == pytest.approx((148 + 132 + 125 + 118 + 152 + 102) / 6)
    assert average_pulse([]) == 0.0
    assert average_pulse([rec(1, "Біг", 45, 1.0, 100)]) == 100.0


def test_longest_workout_and_tie_rules() -> None:
    """Найдовше — 90 хв; за рівної тривалості — раніша дата; потім перший запис."""
    assert longest_workout(RECORDS) == RECORDS[1]
    assert longest_workout([]) is None
    tie = [rec(5, "Біг", 60, 1.0, 100), rec(2, "Йога", 60, 0.0, 90), rec(2, "Ходьба", 60, 2.0, 95)]
    assert longest_workout(tie) == tie[1]


def test_make_summary_accepts_args_default_and_kwargs() -> None:
    """*metrics, типовий min_duration і **labels працюють разом."""
    result = make_summary(RECORDS, "duration", "distance", duration="Тривалість")

    assert result["count"] == 4.0
    assert result["Тривалість"] == 245.0
    assert result["distance"] == pytest.approx(44.0)


def test_make_summary_custom_threshold_and_no_metrics() -> None:
    """Власний поріг і виклик без метрик (лише count)."""
    assert make_summary(RECORDS, min_duration=90) == {"count": 1.0}
    assert make_summary(RECORDS, "pulse", min_duration=90) == {"count": 1.0, "pulse": 132.0}


def test_make_summary_all_filtered_out_keeps_metrics_as_zero() -> None:
    """Якщо всі записи відсіяно, визначені метрики мають значення 0.0."""
    result = make_summary(RECORDS, "duration", min_duration=1000)

    assert result == {"count": 0.0, "duration": 0.0}
    assert make_summary([], "distance") == {"count": 0.0, "distance": 0.0}


def test_make_summary_rejects_unknown_metric_and_stray_label() -> None:
    """Невідома метрика й підпис без метрики — явна ValueError."""
    with pytest.raises(ValueError, match="Невідома метрика: price"):
        make_summary(RECORDS, "price")
    with pytest.raises(ValueError, match="Підпис задано"):
        make_summary(RECORDS, "duration", distance="Дистанція")


def test_analysis_does_not_mutate_input() -> None:
    """Функції аналізу не змінюють вхідний список."""
    snapshot = list(RECORDS)

    select_long(RECORDS)
    distance_by_kind(RECORDS)
    make_summary(RECORDS, "duration")
    longest_workout(RECORDS)

    assert RECORDS == snapshot


def test_make_summary_is_repeatable() -> None:
    """Повторний виклик дає той самий результат: типове значення не накопичує стан."""
    assert make_summary(RECORDS, "duration") == make_summary(RECORDS, "duration")
