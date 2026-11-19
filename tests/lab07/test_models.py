"""Тести моделі: властивості, setter-и, dataclass, спеціальні методи, підтипи, протокол."""

import dataclasses
import datetime as dt
import math

import pytest

from kzp_lab07.models import Cycling, KindLoad, ReportSummary, Running, Training, Workout

DAY = dt.date(2026, 9, 1)


def run(**changes: object) -> Running:
    """Створює бігове тренування зі змінюваними полями."""
    values: dict[str, object] = {
        "date": DAY,
        "kind": "Біг",
        "duration": 45,
        "distance": 7.5,
        "pulse": 148,
    }
    values.update(changes)
    return Running(**values)  # type: ignore[arg-type]


def test_getters_return_constructor_values() -> None:
    """Властивості повертають передані значення; вид очищується від пробілів."""
    training = run(kind="  Біг ")

    assert (training.date, training.kind, training.duration) == (DAY, "Біг", 45)
    assert (training.distance, training.pulse) == (7.5, 148)


def test_base_class_is_abstract() -> None:
    """Базовий клас не створюється напряму: load() — абстрактний."""
    with pytest.raises(TypeError):
        Training(DAY, "Біг", 45, 7.5, 148)  # type: ignore[abstract]


@pytest.mark.parametrize("field", ["duration", "pulse"])
def test_integer_setter_accepts_zero_and_large_values(field: str) -> None:
    """Нуль і велике значення допустимі (межа правила «не від'ємне»)."""
    training = run()

    setattr(training, field, 0)
    assert getattr(training, field) == 0
    setattr(training, field, 10**6)
    assert getattr(training, field) == 10**6


@pytest.mark.parametrize("field", ["duration", "pulse"])
def test_integer_setter_rejects_negative_and_wrong_type(field: str) -> None:
    """Від'ємне — ValueError; не ціле (float, str, bool) — TypeError; стан не змінюється."""
    training = run()
    before = getattr(training, field)

    with pytest.raises(ValueError, match=f"поле {field} не може бути від'ємним"):
        setattr(training, field, -1)
    for bad in (1.5, "45", True, None):
        with pytest.raises(TypeError, match=f"поле {field} має бути цілим числом"):
            setattr(training, field, bad)

    assert getattr(training, field) == before


def test_distance_setter_rules() -> None:
    """Дистанція: нуль і ціле допустимі; від'ємна, NaN, ∞ — ValueError; рядок і bool — TypeError."""
    training = run()

    training.distance = 0
    assert training.distance == 0.0 and isinstance(training.distance, float)
    with pytest.raises(ValueError, match="не може бути від'ємним"):
        training.distance = -0.1
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="скінченним"):
            training.distance = bad
    for bad in ("7.5", True):
        with pytest.raises(TypeError):
            training.distance = bad  # type: ignore[assignment]
    assert training.distance == 0.0


def test_kind_setter_rules() -> None:
    """Вид: непорожній текст; порожній — ValueError; не рядок — TypeError."""
    training = run()

    training.kind = "  Ходьба  "
    assert training.kind == "Ходьба"
    with pytest.raises(ValueError, match="поле kind порожнє"):
        training.kind = "   "
    with pytest.raises(TypeError):
        training.kind = 5  # type: ignore[assignment]
    assert training.kind == "Ходьба"


def test_constructor_validates_through_setters() -> None:
    """Некоректний об'єкт створити неможливо: правила діють у конструкторі."""
    with pytest.raises(ValueError):
        run(duration=-1)
    with pytest.raises(ValueError):
        Cycling(DAY, "Велосипед", 10, math.nan, 100)
    with pytest.raises(TypeError, match="поле date"):
        run(date="2026-09-01")
    with pytest.raises(TypeError, match="поле date"):
        run(date=dt.datetime(2026, 9, 1, 8, 0))


def test_date_is_read_only() -> None:
    """Дата не має setter-а: присвоєння кидає AttributeError."""
    training = run()

    with pytest.raises(AttributeError):
        training.date = dt.date(2026, 9, 2)  # type: ignore[misc]


def test_subtypes_have_different_load_formulas() -> None:
    """Running рахує за пульсом, Cycling — за дистанцією; результати різні."""
    running = Running(DAY, "Біг", 45, 7.5, 148)
    cycling = Cycling(DAY, "Велосипед", 90, 28.4, 132)

    assert running.load() == pytest.approx(66.6)  # 45 * 148 / 100
    assert cycling.load() == pytest.approx(94.2)  # 28.4 * 3 + 90 / 10
    assert running.load() != cycling.load()


def test_load_depends_on_the_right_fields() -> None:
    """Running не залежить від дистанції, Cycling — від пульсу; setter змінює load()."""
    running = run()
    before = running.load()
    running.distance = 100.0
    assert running.load() == before
    running.pulse = 200
    assert running.load() == pytest.approx(90.0)

    cycling = Cycling(DAY, "Велосипед", 60, 10.0, 100)
    base = cycling.load()
    cycling.pulse = 190
    assert cycling.load() == base
    cycling.distance = 20.0
    assert cycling.load() == pytest.approx(66.0)


def test_str_and_repr() -> None:
    """__str__ — для читача; __repr__ — діагностичний, із назвою класу."""
    training = run()

    assert str(training) == "2026-09-01, Біг: 45 хв, 7.50 км, пульс 148"
    assert repr(training) == (
        "Running(date=datetime.date(2026, 9, 1), kind='Біг', duration=45, distance=7.5, pulse=148)"
    )
    assert repr(Cycling(DAY, "Велосипед", 1, 1.0, 1)).startswith("Cycling(")


def test_equality_by_class_and_all_fields() -> None:
    """Дублікати рівні; різні поля чи різні підтипи — ні."""
    assert run() == run()
    assert run() != run(duration=46)
    assert run() != run(kind="Ходьба")
    assert run() != run(distance=7.6)
    assert run() != run(pulse=149)
    assert run() != run(date=dt.date(2026, 9, 2))
    assert Running(DAY, "Біг", 45, 7.5, 148) != Cycling(DAY, "Біг", 45, 7.5, 148)


def test_equality_with_other_type_returns_not_implemented() -> None:
    """__eq__ повертає NotImplemented для чужого типу, а == дає False."""
    assert run().__eq__(5) is NotImplemented
    assert run() != 5
    assert run() != "2026-09-01"


def test_mutable_training_is_unhashable() -> None:
    """Змінюваний об'єкт з __eq__ не хешується."""
    with pytest.raises(TypeError):
        hash(run())
    with pytest.raises(TypeError):
        {run()}


def test_ordering_by_date_then_kind() -> None:
    """sorted() упорядковує за датою, потім за видом; порівняння з чужим типом — TypeError."""
    items = [
        run(date=dt.date(2026, 9, 3)),
        run(date=dt.date(2026, 9, 1), kind="Ходьба"),
        run(date=dt.date(2026, 9, 1), kind="Біг"),
    ]

    ordered = sorted(items)

    assert [(t.date.day, t.kind) for t in ordered] == [(1, "Біг"), (1, "Ходьба"), (3, "Біг")]
    with pytest.raises(TypeError):
        _ = run() < 5  # type: ignore[operator]


def test_summary_dataclass_is_frozen_and_comparable() -> None:
    """ReportSummary незмінний, рівний за значенням, має repr."""
    summary = ReportSummary(2, 1, ("Біг",), 45, 7.5, (("Біг", 7.5),), 100.0, None, ())

    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.total = 3  # type: ignore[misc]
    assert summary == dataclasses.replace(summary)
    assert summary != dataclasses.replace(summary, total=3)
    assert "ReportSummary(total=2" in repr(summary)


def test_kind_load_dataclass_is_frozen_and_hashable() -> None:
    """KindLoad незмінний і хешується (усі поля — прості значення)."""
    item = KindLoad("Біг", 3, 182.6)

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.count = 4  # type: ignore[misc]
    assert item == KindLoad("Біг", 3, 182.6)
    assert len({item, KindLoad("Біг", 3, 182.6)}) == 1


def test_protocol_matches_subtypes_and_foreign_duck() -> None:
    """Running, Cycling і сторонній клас із потрібними членами відповідають Workout."""

    class Duck:
        date, kind, duration, distance, pulse = DAY, "Йога", 50, 0.0, 118

        def load(self) -> float:
            return 1.0

    assert isinstance(run(), Workout)
    assert isinstance(Cycling(DAY, "Велосипед", 1, 1.0, 1), Workout)
    assert isinstance(Duck(), Workout)
    assert not isinstance(object(), Workout)
