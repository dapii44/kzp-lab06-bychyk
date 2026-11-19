"""Тести аналізу: працює через протокол, без перевірки конкретних класів."""

import datetime as dt
import inspect

import pytest

from kzp_lab07 import analysis
from kzp_lab07.analysis import (
    average_pulse,
    distance_by_kind,
    load_by_kind,
    longest_workout,
    select_long,
    summarize,
    unique_kinds,
)
from kzp_lab07.models import Cycling, KindLoad, Running


def day(number: int) -> dt.date:
    """Повертає дату вересня 2026."""
    return dt.date(2026, 9, number)


TRAININGS = [
    Running(day(1), "Біг", 45, 7.5, 148),
    Cycling(day(2), "Велосипед", 90, 28.4, 132),
    Running(day(3), "Плавання", 30, 1.2, 125),
    Running(day(4), "Силове, зал", 60, 0.0, 118),
    Running(day(5), "Біг", 50, 8.1, 152),
    Running(day(6), "Ходьба", 44, 3.4, 102),
]


class Duck:
    """Сторонній клас без спільного предка: лише потрібні члени протоколу."""

    def __init__(self, kind: str, duration: int, distance: float, pulse: int, load: float):
        self.date, self.kind, self.duration = day(7), kind, duration
        self.distance, self.pulse, self._load = distance, pulse, load

    def load(self) -> float:
        return self._load


def test_analysis_source_has_no_type_checks() -> None:
    """Модуль analysis не містить isinstance/type() і назв конкретних підтипів."""
    source = inspect.getsource(analysis)

    for forbidden in ("isinstance", "type(", "Running", "Cycling"):
        assert forbidden not in source


def test_select_long_boundary() -> None:
    """45 хв входить, 44 хв — ні; працює для обох підтипів."""
    selected = select_long(TRAININGS)

    assert [t.date.day for t in selected] == [1, 2, 4, 5]
    assert any(isinstance(t, Cycling) for t in selected)


def test_select_long_custom_and_empty() -> None:
    """Власний поріг і порожній вхід."""
    assert [t.date.day for t in select_long(TRAININGS, 90)] == [2]
    assert select_long([]) == []


def test_unique_kinds_and_distance_by_kind() -> None:
    """Множина без повторів; словник відсортований і не залежить від порядку входу."""
    assert unique_kinds(TRAININGS) == {"Біг", "Велосипед", "Плавання", "Силове, зал", "Ходьба"}
    totals = distance_by_kind(TRAININGS)
    assert list(totals) == sorted(totals)
    assert totals["Біг"] == pytest.approx(15.6)
    assert distance_by_kind(list(reversed(TRAININGS))) == totals
    assert distance_by_kind([]) == {}


def test_average_pulse_and_longest() -> None:
    """Середній пульс; найдовше й правило рівності."""
    assert average_pulse(TRAININGS) == pytest.approx((148 + 132 + 125 + 118 + 152 + 102) / 6)
    assert average_pulse([]) == 0.0
    assert longest_workout(TRAININGS) is TRAININGS[1]
    assert longest_workout([]) is None
    tie = [Running(day(5), "Біг", 60, 1.0, 100), Running(day(2), "Йога", 60, 0.0, 90)]
    assert longest_workout(tie) is tie[1]


def test_load_by_kind_is_polymorphic() -> None:
    """Навантаження за видом рахується викликом load() кожного об'єкта."""
    result = load_by_kind(TRAININGS)

    assert [item.kind for item in result] == sorted({t.kind for t in TRAININGS})
    biy = next(item for item in result if item.kind == "Біг")
    assert biy.count == 2
    assert biy.total_load == pytest.approx(45 * 148 / 100 + 50 * 152 / 100)
    cycling = next(item for item in result if item.kind == "Велосипед")
    assert cycling.total_load == pytest.approx(94.2)
    assert load_by_kind([]) == ()


def test_duck_typed_object_works_without_changes_in_analysis() -> None:
    """Сторонній об'єкт із членами протоколу обробляється всіма функціями аналізу."""
    mixed = [*TRAININGS, Duck("Йога", 50, 0.0, 118, 42.0)]

    assert "Йога" in unique_kinds(mixed)
    assert any(isinstance(w, Duck) for w in select_long(mixed))
    assert KindLoad("Йога", 1, 42.0) in load_by_kind(mixed)
    assert summarize(mixed).total == 7


def test_summarize_values_on_control_like_data() -> None:
    """Підсумок: лічильники, суми, відсортовані кортежі."""
    summary = summarize(TRAININGS)

    assert (summary.total, summary.selected) == (6, 4)
    assert summary.kinds == tuple(sorted(summary.kinds))
    assert summary.selected_minutes == 245
    assert summary.selected_distance == pytest.approx(44.0)
    assert [kind for kind, _ in summary.distance_by_kind] == ["Біг", "Велосипед", "Силове, зал"]
    assert summary.longest is TRAININGS[1]


def test_summarize_empty_and_filtered_out() -> None:
    """Порожній вхід і порожній відбір дають нулі без винятків."""
    empty = summarize([])
    assert (empty.total, empty.selected, empty.average_pulse) == (0, 0, 0.0)
    assert empty.longest is None and empty.load_by_kind == () and empty.kinds == ()

    none_selected = summarize(TRAININGS, min_duration=1000)
    assert none_selected.selected == 0
    assert none_selected.selected_minutes == 0 and none_selected.distance_by_kind == ()
    assert none_selected.average_pulse > 0


def test_analysis_does_not_mutate_input() -> None:
    """Функції аналізу не змінюють вхідний список і об'єкти."""
    snapshot = list(TRAININGS)
    pulses = [t.pulse for t in TRAININGS]

    summarize(TRAININGS)
    load_by_kind(TRAININGS)

    assert TRAININGS == snapshot
    assert [t.pulse for t in TRAININGS] == pulses
