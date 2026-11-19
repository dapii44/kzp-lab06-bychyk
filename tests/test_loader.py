"""Тести завантаження й перетворення CSV."""

from datetime import date
from pathlib import Path

import pytest

from kzp_lab06.errors import DataError
from kzp_lab06.loader import load_records, parse_row

from .conftest import HEADER, ROOT


def test_loads_control_file_with_typed_values() -> None:
    """Контрольний файл дає 7 записів з типами date, str, int, float, int."""
    records = load_records(ROOT / "data" / "input.csv")

    assert len(records) == 7
    first = records[0]
    assert first == {
        "date": date(2026, 9, 1),
        "kind": "Біг",
        "duration": 45,
        "distance": 7.5,
        "pulse": 148,
    }
    assert isinstance(first["duration"], int) and isinstance(first["distance"], float)


def test_text_field_with_comma_is_kept(write_csv) -> None:
    """Поле «Силове, зал» у лапках лишається одним полем."""
    path = write_csv(HEADER + '2026-09-04,"Силове, зал",60,0.00,118\n')

    assert load_records(path)[0]["kind"] == "Силове, зал"


def test_header_only_file_gives_empty_list(write_csv) -> None:
    """Файл лише із заголовком — коректний порожній набір."""
    assert load_records(write_csv(HEADER)) == []


def test_file_without_header_is_error(write_csv) -> None:
    """Зовсім порожній файл (0 байтів) — помилка: заголовка немає."""
    with pytest.raises(DataError, match="відсутній заголовок"):
        load_records(write_csv(""))


def test_missing_column_is_reported(write_csv) -> None:
    """Відсутній стовпець називається в повідомленні."""
    path = write_csv("date,kind,duration,distance\n2026-09-01,Біг,45,7.5\n")

    with pytest.raises(DataError, match="відсутні стовпці: pulse"):
        load_records(path)


def test_extra_column_is_reported(write_csv) -> None:
    """Зайвий стовпець відхиляється з назвою."""
    path = write_csv("date,kind,duration,distance,pulse,note\n2026-09-01,Біг,45,7.5,148,x\n")

    with pytest.raises(DataError, match="зайві стовпці: note"):
        load_records(path)


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("2026-09-01,Біг,сорок,7.5,148", "Рядок 2: поле duration має бути цілим числом"),
        ("2026-09-01,Біг,45,abc,148", "Рядок 2: поле distance має бути числом"),
        ("2026-09-01,Біг,45,7.5,1.5", "Рядок 2: поле pulse має бути цілим числом"),
        ("2026-09-01,Біг,-1,7.5,148", "Рядок 2: поле duration не може бути від'ємним"),
        ("2026-09-01,Біг,45,-0.5,148", "Рядок 2: поле distance не може бути від'ємним"),
        ("2026-09-01,Біг,45,nan,148", "Рядок 2: поле distance має бути скінченним числом"),
        ("2026-09-01,Біг,45,inf,148", "Рядок 2: поле distance має бути скінченним числом"),
        ("2026-13-45,Біг,45,7.5,148", "Рядок 2: поле date має бути датою"),
        ("2026-09-01,   ,45,7.5,148", "Рядок 2: поле kind порожнє"),
    ],
)
def test_bad_values_report_row_and_field(write_csv, row: str, message: str) -> None:
    """Помилка містить номер рядка й назву поля."""
    with pytest.raises(DataError, match=message):
        load_records(write_csv(HEADER + row + "\n"))


def test_bad_number_keeps_root_cause(write_csv) -> None:
    """raise ... from зберігає першопричину ValueError."""
    with pytest.raises(DataError) as info:
        load_records(write_csv(HEADER + "2026-09-01,Біг,сорок,7.5,148\n"))

    assert isinstance(info.value.__cause__, ValueError)


def test_missing_value_in_short_row(write_csv) -> None:
    """Короткий рядок: DictReader дає None, програма повідомляє про відсутнє значення."""
    with pytest.raises(DataError, match="Рядок 2: відсутнє значення поля pulse"):
        load_records(write_csv(HEADER + "2026-09-01,Біг,45,7.5\n"))


def test_too_many_fields_in_row(write_csv) -> None:
    """Надлишкові значення в рядку відхиляються."""
    with pytest.raises(DataError, match="Рядок 2: забагато полів"):
        load_records(write_csv(HEADER + "2026-09-01,Біг,45,7.5,148,зайве\n"))


def test_row_number_is_physical_line_after_blank_line(write_csv) -> None:
    """Порожній рядок пропускається, але нумерація лишається фізичною."""
    text = HEADER + "2026-09-01,Біг,45,7.5,148\n\n2026-09-02,Біг,abc,7.5,148\n"

    with pytest.raises(DataError, match="Рядок 4: поле duration"):
        load_records(write_csv(text))


def test_duplicate_rows_are_kept(write_csv) -> None:
    """Ідентичні рядки лишаються окремими записами."""
    row = "2026-09-01,Біг,45,7.5,148\n"

    assert len(load_records(write_csv(HEADER + row + row))) == 2


def test_boundary_numbers_are_accepted(write_csv) -> None:
    """Нульові значення допустимі."""
    record = load_records(write_csv(HEADER + "2026-09-01,Йога,0,0,0\n"))[0]

    assert (record["duration"], record["distance"], record["pulse"]) == (0, 0.0, 0)


def test_missing_file_is_data_error_with_os_cause(tmp_path: Path) -> None:
    """Відсутній файл — DataError з OSError як першопричиною."""
    with pytest.raises(DataError, match="Не вдалося прочитати файл") as info:
        load_records(tmp_path / "немає.csv")

    assert isinstance(info.value.__cause__, OSError)


def test_not_utf8_file_is_data_error(tmp_path: Path) -> None:
    """Файл не в UTF-8 дає DataError, а не сирий UnicodeDecodeError."""
    path = tmp_path / "bad.csv"
    path.write_bytes(HEADER.encode() + b"2026-09-01,\xff\xfe,45,7.5,148\n")

    with pytest.raises(DataError) as info:
        load_records(path)

    assert isinstance(info.value.__cause__, UnicodeDecodeError)


def test_input_file_is_not_modified(write_csv) -> None:
    """Читання не змінює вхідний файл."""
    path = write_csv(HEADER + "2026-09-01,Біг,45,7.5,148\n")
    before = path.read_bytes()

    load_records(path)

    assert path.read_bytes() == before


def test_parse_row_rejects_extra_key() -> None:
    """parse_row відхиляє ключ None (надлишкові поля DictReader)."""
    row = {
        "date": "2026-09-01",
        "kind": "Біг",
        "duration": "45",
        "distance": "1",
        "pulse": "1",
        None: ["x"],
    }  # type: ignore[dict-item]

    with pytest.raises(DataError, match="забагато"):
        parse_row(row, 5)  # type: ignore[arg-type]
