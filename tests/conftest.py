"""Спільні допоміжні функції тестів."""

from pathlib import Path

import pytest

HEADER = "date,kind,duration,distance,pulse\n"
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def write_csv(tmp_path: Path):
    """Повертає функцію, що записує CSV-текст (UTF-8, ``\\n``) у тимчасовий файл."""

    def _write(text: str, name: str = "input.csv") -> Path:
        path = tmp_path / name
        path.write_bytes(text.encode("utf-8"))
        return path

    return _write
