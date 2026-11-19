"""Тести завантаження CSV в об'єкти."""

import datetime as dt
from pathlib import Path

import pytest

from kzp_lab07.errors import DataError
from kzp_lab07.loader import build_training, load_trainings
from kzp_lab07.models import Cycling, Running

from ..conftest import HEADER, ROOT


def test_control_file_gives_objects_of_both_subtypes() -> None:
    """Контрольний файл: 7 об'єктів, Велосипед — Cycling, решта — Running."""
    trainings = load_trainings(ROOT / "data" / "input.csv")

    assert len(trainings) == 7
    assert [type(t) for t in trainings].count(Cycling) == 1
    assert [type(t) for t in trainings].count(Running) == 6
    first = trainings[0]
    assert isinstance(first, Running)
    assert (first.date, first.kind, first.duration) == (dt.date(2026, 9, 1), "Біг", 45)
    assert isinstance(first.distance, float) and isinstance(first.pulse, int)


def test_kind_choice_is_case_insensitive(write_csv) -> None:
    """Вид «велосипед» у будь-якому регістрі дає Cycling."""
    path = write_csv(HEADER + "2026-09-01,ВЕЛОСИПЕД,60,20.0,130\n2026-09-02,Біг,30,5.0,150\n")

    first, second = load_trainings(path)

    assert isinstance(first, Cycling) and isinstance(second, Running)


def test_text_with_comma_is_kept(write_csv) -> None:
    """Поле «Силове, зал» у лапках лишається одним полем."""
    path = write_csv(HEADER + '2026-09-04,"Силове, зал",60,0.00,118\n')

    assert load_trainings(path)[0].kind == "Силове, зал"


def test_header_only_and_no_header(write_csv) -> None:
    """Лише заголовок — порожній список; порожній файл — DataError."""
    assert load_trainings(write_csv(HEADER)) == []
    with pytest.raises(DataError, match="відсутній заголовок"):
        load_trainings(write_csv("", "empty.csv"))


def test_header_problems(write_csv) -> None:
    """Відсутній і зайвий стовпці називаються в повідомленні."""
    with pytest.raises(DataError, match="відсутні стовпці: pulse"):
        load_trainings(write_csv("date,kind,duration,distance\n2026-09-01,Біг,45,7.5\n"))
    with pytest.raises(DataError, match="зайві стовпці: note"):
        load_trainings(write_csv(HEADER.strip() + ",note\n2026-09-01,Біг,45,7.5,148,x\n"))


BAD_ROWS = [
    ("2026-09-01,Біг,сорок,7.5,148", "Рядок 2: поле duration має бути цілим числом"),
    ("2026-09-01,Біг,45,abc,148", "Рядок 2: поле distance має бути числом"),
    ("2026-09-01,Біг,45,7.5,1.5", "Рядок 2: поле pulse має бути цілим числом"),
    ("2026-09-01,Біг,-1,7.5,148", "Рядок 2: поле duration не може бути від'ємним"),
    ("2026-09-01,Біг,45,-0.5,148", "Рядок 2: поле distance не може бути від'ємним"),
    ("2026-09-01,Біг,45,7.5,-3", "Рядок 2: поле pulse не може бути від'ємним"),
    ("2026-09-01,Біг,45,nan,148", "Рядок 2: поле distance має бути скінченним числом"),
    ("2026-09-01,Біг,45,inf,148", "Рядок 2: поле distance має бути скінченним числом"),
    ("2026-13-45,Біг,45,7.5,148", "Рядок 2: поле date має бути датою"),
    ("2026-09-01,   ,45,7.5,148", "Рядок 2: поле kind порожнє"),
    ("2026-09-01,Біг,45,7.5", "Рядок 2: відсутнє значення поля pulse"),
    ("2026-09-01,Біг,45,7.5,148,зайве", "Рядок 2: забагато полів"),
]


@pytest.mark.parametrize(("row", "message"), BAD_ROWS)
def test_bad_rows_report_line_and_field(write_csv, row: str, message: str) -> None:
    """Помилка містить номер рядка й назву поля."""
    with pytest.raises(DataError, match=message):
        load_trainings(write_csv(HEADER + row + "\n"))


def test_model_error_keeps_root_cause(write_csv) -> None:
    """Правило моделі (setter) зберігається як __cause__ у DataError."""
    with pytest.raises(DataError) as info:
        load_trainings(write_csv(HEADER + "2026-09-01,Біг,-1,7.5,148\n"))

    assert isinstance(info.value.__cause__, ValueError)


def test_row_number_is_physical_line_after_blank_line(write_csv) -> None:
    """Порожній рядок пропускається, але нумерація лишається фізичною."""
    text = HEADER + "2026-09-01,Біг,45,7.5,148\n\n2026-09-02,Біг,abc,7.5,148\n"

    with pytest.raises(DataError, match="Рядок 4: поле duration"):
        load_trainings(write_csv(text))


def test_duplicates_are_kept_and_equal(write_csv) -> None:
    """Ідентичні рядки дають два рівні об'єкти."""
    row = "2026-09-01,Біг,45,7.5,148\n"

    first, second = load_trainings(write_csv(HEADER + row + row))

    assert first == second and first is not second


def test_zero_boundary_row_is_accepted(write_csv) -> None:
    """Нульові значення — коректний запис (межа setter-ів)."""
    training = load_trainings(write_csv(HEADER + "2026-09-01,Йога,0,0,0\n"))[0]

    assert (training.duration, training.distance, training.pulse) == (0, 0.0, 0)


def test_file_errors(tmp_path: Path) -> None:
    """Відсутній і не-UTF-8 файли — DataError з системною причиною."""
    with pytest.raises(DataError, match="Не вдалося прочитати файл") as missing:
        load_trainings(tmp_path / "немає.csv")
    assert isinstance(missing.value.__cause__, OSError)

    binary = tmp_path / "bad.csv"
    binary.write_bytes(HEADER.encode() + b"2026-09-01,\xff\xfe,45,7.5,148\n")
    with pytest.raises(DataError) as notutf:
        load_trainings(binary)
    assert isinstance(notutf.value.__cause__, UnicodeDecodeError)


def test_build_training_rejects_extra_key() -> None:
    """Надлишкові поля DictReader (ключ None) відхиляються."""
    row = {
        "date": "2026-09-01",
        "kind": "Біг",
        "duration": "45",
        "distance": "1",
        "pulse": "1",
        None: ["x"],
    }  # type: ignore[dict-item]

    with pytest.raises(DataError, match="забагато"):
        build_training(row, 5)  # type: ignore[arg-type]


def test_loader_does_not_modify_input(write_csv) -> None:
    """Читання не змінює вхідний файл."""
    path = write_csv(HEADER + "2026-09-01,Біг,45,7.5,148\n")
    before = path.read_bytes()

    load_trainings(path)

    assert path.read_bytes() == before
