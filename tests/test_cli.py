"""Тести командного рядка: коди завершення, повідомлення, запуск як модуля."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kzp_lab06 import __version__
from kzp_lab06.cli import EXIT_DATA_ERROR, EXIT_OK, main

from .conftest import HEADER, ROOT


def test_success_writes_report_and_returns_zero(tmp_path: Path, capsys) -> None:
    """Успіх: код 0, звіт записано, у stdout — повідомлення."""
    output = tmp_path / "out" / "summary.txt"

    code = main([str(ROOT / "data" / "input.csv"), str(output)])

    assert code == EXIT_OK
    assert output.read_text(encoding="utf-8").startswith("Звіт про тренування\n")
    assert "Звіт записано" in capsys.readouterr().out


def test_corrupted_csv_returns_two_with_message_on_stderr(
    tmp_path: Path, write_csv, capsys
) -> None:
    """Пошкоджений CSV: код 2, пояснення в stderr, звіт не створено."""
    source = write_csv(HEADER + "2026-09-01,Біг,сорок,7.5,148\n")
    output = tmp_path / "summary.txt"

    code = main([str(source), str(output)])

    assert code == EXIT_DATA_ERROR
    assert "Помилка даних: Рядок 2: поле duration має бути цілим числом" in capsys.readouterr().err
    assert not output.exists()


def test_missing_input_returns_two(tmp_path: Path, capsys) -> None:
    """Відсутній вхідний файл — очікувана помилка даних, а не traceback."""
    code = main([str(tmp_path / "немає.csv"), str(tmp_path / "r.txt")])

    assert code == EXIT_DATA_ERROR
    assert "Не вдалося прочитати файл" in capsys.readouterr().err


def test_unwritable_output_returns_two(tmp_path: Path, capsys) -> None:
    """Неможливий вихідний шлях (батько — файл) — код 2."""
    blocker = tmp_path / "blocker"
    blocker.write_text("файл", encoding="utf-8")

    code = main([str(ROOT / "data" / "input.csv"), str(blocker / "r.txt")])

    assert code == EXIT_DATA_ERROR
    assert "Не вдалося записати звіт" in capsys.readouterr().err


def test_custom_min_duration(tmp_path: Path) -> None:
    """Параметр --min-duration змінює відбір у звіті."""
    output = tmp_path / "r.txt"

    assert main([str(ROOT / "data" / "input.csv"), str(output), "--min-duration", "90"]) == 0

    assert "Відібрано (тривалість >= 90 хв): 1" in output.read_text(encoding="utf-8")


def test_input_file_is_unchanged(tmp_path: Path) -> None:
    """CLI не змінює вхідний файл."""
    source = ROOT / "data" / "input.csv"
    before = hashlib.sha256(source.read_bytes()).hexdigest()

    main([str(source), str(tmp_path / "r.txt")])

    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_missing_arguments_exit_two() -> None:
    """argparse без обов'язкових аргументів завершується кодом 2."""
    with pytest.raises(SystemExit) as info:
        main([])

    assert info.value.code == 2


def test_version_option(capsys) -> None:
    """--version друкує версію пакета."""
    with pytest.raises(SystemExit) as info:
        main(["--version"])

    assert info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_run_as_module_success_and_failure(tmp_path: Path, write_csv) -> None:
    """python -m kzp_lab06.cli: код 0 для успіху, 2 і UTF-8 повідомлення для помилки."""
    ok = subprocess.run(
        [
            sys.executable,
            "-m",
            "kzp_lab06.cli",
            str(ROOT / "data" / "input.csv"),
            str(tmp_path / "r.txt"),
        ],
        capture_output=True,
        check=False,
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert ok.returncode == 0

    bad = write_csv(HEADER + "2026-09-01,Біг,-5,7.5,148\n")
    failed = subprocess.run(
        [sys.executable, "-m", "kzp_lab06.cli", str(bad), str(tmp_path / "x.txt")],
        capture_output=True,
        check=False,
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert failed.returncode == 2
    assert "поле duration не може бути від'ємним" in failed.stderr.decode("utf-8")
