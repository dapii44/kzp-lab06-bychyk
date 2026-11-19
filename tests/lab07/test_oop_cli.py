"""Тести CLI лабораторної № 7 і еквівалентності зі звітом лабораторної № 6."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kzp_lab06.cli import main as main06
from kzp_lab07 import __version__
from kzp_lab07.analysis import summarize
from kzp_lab07.cli import EXIT_DATA_ERROR, EXIT_OK, main
from kzp_lab07.reporting import format_report, write_report

from ..conftest import HEADER, ROOT

CONTROL = ROOT / "data" / "input.csv"
OOP_DATA = ROOT / "data" / "workouts-oop.csv"


def test_old_and_new_reports_are_identical(tmp_path: Path) -> None:
    """Той самий вхід: звіт на словниках (лаб. 6) і на об'єктах (лаб. 7) збігаються побайтово."""
    old, new = tmp_path / "old.txt", tmp_path / "new.txt"

    assert main06([str(CONTROL), str(old)]) == 0
    assert main([str(CONTROL), str(new)]) == EXIT_OK

    assert old.read_bytes() == new.read_bytes()


def test_load_block_is_an_extension_of_the_base_report(tmp_path: Path) -> None:
    """З --load базовий текст не змінюється, додається лише блок навантаження."""
    base, extended = tmp_path / "base.txt", tmp_path / "ext.txt"
    main([str(CONTROL), str(base)])
    main([str(CONTROL), str(extended), "--load"])

    base_text, ext_text = base.read_text(encoding="utf-8"), extended.read_text(encoding="utf-8")

    assert ext_text.startswith(base_text)
    assert "Навантаження за видом (load):" in ext_text[len(base_text) :]


def test_example_report_matches_committed_file(tmp_path: Path) -> None:
    """Приклад у reports/ відповідає поточній програмі (звіт відтворюваний)."""
    output = tmp_path / "out.txt"

    assert main([str(OOP_DATA), str(output), "--load"]) == EXIT_OK

    expected = (ROOT / "reports" / "example-oop-summary.txt").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_load_values_for_both_subtypes(tmp_path: Path) -> None:
    """У прикладі Велосипед (Cycling) = 227.90, Біг (Running) = 142.60; дублікат враховано."""
    output = tmp_path / "out.txt"
    main([str(OOP_DATA), str(output), "--load"])
    text = output.read_text(encoding="utf-8")

    assert "  Велосипед: 227.90 (3 трен.)" in text
    assert "  Біг: 142.60 (2 трен.)" in text
    assert "  Йога: 0.00 (1 трен.)" in text


def test_custom_threshold(tmp_path: Path) -> None:
    """--min-duration змінює відбір."""
    output = tmp_path / "out.txt"
    main([str(CONTROL), str(output), "--min-duration", "90"])

    assert "Відібрано (тривалість >= 90 хв): 1" in output.read_text(encoding="utf-8")


def test_bad_row_gives_exit_two_without_report(tmp_path: Path, write_csv, capsys) -> None:
    """Помилка даних: код 2, повідомлення з рядком у stderr, звіт не створюється."""
    source = write_csv(HEADER + "2026-09-01,Біг,-5,7.5,148\n")
    output = tmp_path / "out.txt"

    code = main([str(source), str(output)])

    captured = capsys.readouterr()
    assert code == EXIT_DATA_ERROR
    assert "Рядок 2: поле duration не може бути від'ємним" in captured.err
    assert captured.out == "" and not output.exists()


def test_missing_input_and_unwritable_output(tmp_path: Path, capsys) -> None:
    """Відсутній вхід і неможливий вихід (каталог замість файла) — код 2."""
    assert main([str(tmp_path / "немає.csv"), str(tmp_path / "o.txt")]) == EXIT_DATA_ERROR
    assert "Не вдалося прочитати файл" in capsys.readouterr().err

    assert main([str(CONTROL), str(tmp_path)]) == EXIT_DATA_ERROR
    assert "Не вдалося записати звіт" in capsys.readouterr().err


def test_empty_and_header_only_inputs(tmp_path: Path, write_csv, capsys) -> None:
    """Лише заголовок — звіт із нулями; порожній файл — код 2."""
    output = tmp_path / "out.txt"

    assert main([str(write_csv(HEADER)), str(output), "--load"]) == EXIT_OK
    text = output.read_text(encoding="utf-8")
    assert "Записів у файлі: 0" in text and "Найдовше тренування: немає даних" in text
    assert "Середній пульс: 0.00" in text and "Види тренувань: немає" in text

    assert main([str(write_csv("", "e.csv")), str(output)]) == EXIT_DATA_ERROR
    assert "відсутній заголовок" in capsys.readouterr().err


def test_input_file_is_not_modified(tmp_path: Path) -> None:
    """Вхідний CSV після запуску має той самий хеш."""
    before = hashlib.sha256(CONTROL.read_bytes()).hexdigest()

    main([str(CONTROL), str(tmp_path / "out.txt"), "--load"])

    assert hashlib.sha256(CONTROL.read_bytes()).hexdigest() == before


def test_report_is_deterministic(tmp_path: Path) -> None:
    """Два запуски дають однакові байти (без часу й випадковості)."""
    first, second = tmp_path / "a.txt", tmp_path / "b.txt"
    main([str(OOP_DATA), str(first), "--load"])
    main([str(OOP_DATA), str(second), "--load"])

    assert first.read_bytes() == second.read_bytes()
    assert b"\r" not in first.read_bytes()


def test_format_and_write_are_separate_steps(tmp_path: Path) -> None:
    """format_report повертає текст без побічних ефектів, write_report лише записує."""
    from kzp_lab07.loader import load_trainings

    summary = summarize(load_trainings(CONTROL))
    text = format_report(summary, 45)

    assert not (tmp_path / "x.txt").exists()
    write_report(tmp_path / "sub" / "x.txt", text)
    assert (tmp_path / "sub" / "x.txt").read_text(encoding="utf-8") == text


def test_version_option(capsys) -> None:
    """--version друкує версію й завершує програму кодом 0."""
    with pytest.raises(SystemExit) as info:
        main(["--version"])

    assert info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_run_as_module_in_subprocess(tmp_path: Path) -> None:
    """Запуск ``python -m kzp_lab07.cli`` працює як справжня програма."""
    output = tmp_path / "out.txt"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

    result = subprocess.run(
        [sys.executable, "-m", "kzp_lab07.cli", str(CONTROL), str(output), "--load"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Навантаження за видом" in output.read_text(encoding="utf-8")
