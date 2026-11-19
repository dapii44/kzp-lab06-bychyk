"""Тести формування й запису звіту."""

import random
from pathlib import Path

import pytest

from kzp_lab06.errors import DataError
from kzp_lab06.loader import load_records
from kzp_lab06.reporting import format_report, write_report

from .conftest import ROOT

EXPECTED = """Звіт про тренування
Записів у файлі: 7
Відібрано (тривалість >= 45 хв): 4
Види тренувань: Біг; Велосипед; Плавання; Силове, зал; Ходьба
Сума за відібраними: Тривалість, хв = 245.00; Дистанція, км = 44.00
Дистанція за видом (відібрані):
  Біг: 15.60 км
  Велосипед: 28.40 км
  Силове, зал: 0.00 км
Середній пульс: 133.86
Найдовше тренування: 2026-09-02, Велосипед, 90 хв, 28.40 км, пульс 132
"""


def test_report_for_control_file_matches_expected_text() -> None:
    """Повний звіт для контрольного файла збігається з очікуваним текстом."""
    assert format_report(load_records(ROOT / "data" / "input.csv")) == EXPECTED


def test_committed_example_matches_report() -> None:
    """Приклад reports/example-summary.txt відповідає тому, що програма генерує."""
    example = (ROOT / "reports" / "example-summary.txt").read_text(encoding="utf-8")

    assert example == EXPECTED


def test_report_is_independent_of_input_order() -> None:
    """Звіт детермінований: перемішування рядків не змінює текст."""
    records = load_records(ROOT / "data" / "input.csv")
    shuffled = records[:]
    random.Random(7).shuffle(shuffled)

    assert format_report(shuffled) == format_report(records)


def test_report_for_empty_records() -> None:
    """Порожній вхід: явні рядки «немає», нулі, без винятків."""
    text = format_report([])

    assert "Записів у файлі: 0" in text
    assert "Види тренувань: немає" in text
    assert "  немає записів" in text
    assert "Середній пульс: 0.00" in text
    assert "Найдовше тренування: немає даних" in text


def test_report_when_filter_removes_everything() -> None:
    """Відбір порожній, але записи є: нулі в сумах і середній пульс за всіма записами."""
    records = load_records(ROOT / "data" / "input.csv")

    text = format_report(records, min_duration=1000)

    assert "Відібрано (тривалість >= 1000 хв): 0" in text
    assert "Тривалість, хв = 0.00; Дистанція, км = 0.00" in text
    assert "Середній пульс: 133.86" in text


def test_write_report_utf8_and_lf(tmp_path: Path) -> None:
    """Файл у UTF-8, кінець рядка \\n (без \\r), каталог створено."""
    target = tmp_path / "nested" / "report.txt"

    write_report(target, "Готово\nдруге\n")

    assert target.read_bytes() == "Готово\nдруге\n".encode()
    assert b"\r" not in target.read_bytes()


def test_write_report_replaces_existing_file(tmp_path: Path) -> None:
    """Повторний запис повністю замінює старий вміст."""
    target = tmp_path / "report.txt"
    write_report(target, "довгий старий вміст\n")

    write_report(target, "новий\n")

    assert target.read_text(encoding="utf-8") == "новий\n"


def test_write_report_failure_is_data_error(tmp_path: Path) -> None:
    """Каталог неможливо створити (батько — файл): DataError із OSError як причиною."""
    blocker = tmp_path / "blocker"
    blocker.write_text("файл", encoding="utf-8")

    with pytest.raises(DataError, match="Не вдалося записати звіт") as info:
        write_report(blocker / "report.txt", "x")

    assert isinstance(info.value.__cause__, OSError)
