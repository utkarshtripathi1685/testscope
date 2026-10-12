"""Tests for Git change detection."""

import subprocess
from pathlib import Path

import pytest

from testscope.git_analyzer import get_changed_files


def run_git(path: Path, *args: str) -> None:
    """Run a Git command in a temporary repository."""
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary Git repository with one committed file."""
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "test@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")

    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    run_git(tmp_path, "add", "app.py")
    run_git(tmp_path, "commit", "-m", "initial commit")

    return tmp_path


def test_detects_modified_file(git_repo: Path) -> None:
    """Detect a tracked file modified in the working tree."""
    (git_repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")

    changes = get_changed_files(git_repo)

    assert [(item.path, item.status) for item in changes] == [
        ("app.py", "modified")
    ]


def test_detects_untracked_file_as_added(git_repo: Path) -> None:
    """Detect a new, untracked file."""
    (git_repo / "new_module.py").write_text("VALUE = 3\n", encoding="utf-8")

    changes = get_changed_files(git_repo)

    assert any(
        item.path == "new_module.py" and item.status == "added"
        for item in changes
    )


def test_detects_deleted_file(git_repo: Path) -> None:
    """Detect a tracked file deleted from the working tree."""
    (git_repo / "app.py").unlink()

    changes = get_changed_files(git_repo)

    assert any(
        item.path == "app.py" and item.status == "deleted"
        for item in changes
    )


def test_rejects_invalid_repository(tmp_path: Path) -> None:
    """Reject a directory that is not inside a Git repository."""
    with pytest.raises(ValueError, match="Not a valid Git repository"):
        get_changed_files(tmp_path)
