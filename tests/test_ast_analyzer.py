"""Tests for AST-based import extraction."""

from pathlib import Path

from testscope.ast_analyzer import extract_imports


def test_extracts_regular_imports(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "import os\nimport json\nimport package.module\n",
        encoding="utf-8",
    )

    assert extract_imports(source) == {
        "os",
        "json",
        "package.module",
    }


def test_extracts_from_imports(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "from pathlib import Path\nfrom package import helper\n",
        encoding="utf-8",
    )

    assert extract_imports(source) == {"pathlib", "package"}


def test_extracts_relative_imports(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "from . import helper\nfrom ..services import auth\n",
        encoding="utf-8",
    )

    assert extract_imports(source) == {".", "..services"}


def test_returns_empty_set_for_invalid_syntax(tmp_path: Path) -> None:
    source = tmp_path / "broken.py"
    source.write_text("def broken(:\n", encoding="utf-8")

    assert extract_imports(source) == set()


def test_returns_empty_set_for_missing_file(tmp_path: Path) -> None:
    assert extract_imports(tmp_path / "missing.py") == set()