"""Тести метаданих пакета й відсутності побічних ефектів під час імпорту."""

import importlib
import tomllib

from .conftest import ROOT


def test_version_matches_pyproject() -> None:
    """Версія в коді збігається з pyproject.toml."""
    import kzp_lab06

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert kzp_lab06.__version__ == data["project"]["version"]


def test_importing_modules_has_no_side_effects(capsys) -> None:
    """Імпорт модулів нічого не друкує й не запускає CLI."""
    for name in ("loader", "analysis", "reporting", "cli", "errors"):
        importlib.import_module(f"kzp_lab06.{name}")

    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
