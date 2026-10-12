"""Git change detection for TestScope."""

from dataclasses import dataclass
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo


@dataclass(frozen=True)
class FileChange:
    """Represent a file changed in a Git repository."""

    path: str
    status: str
    old_path: str | None = None


def get_changed_files(
    repo_path: str | Path = ".",
    base: str | None = None,
) -> list[FileChange]:
    """Return files changed in the working tree or against a base revision."""
    try:
        repo = Repo(repo_path, search_parent_directories=False)
    except (InvalidGitRepositoryError, NoSuchPathError) as exc:
        raise ValueError(f"Not a valid Git repository: {repo_path}") from exc

    changes: list[FileChange] = []

    if base is None:
        # Unstaged changes.
        for item in repo.index.diff(None):
            path = item.b_path or item.a_path
            if path is not None:
                status = "deleted" if item.deleted_file else "modified"
                changes.append(FileChange(path=path, status=status))

        # Staged changes.
        for item in repo.index.diff("HEAD"):
            path = item.b_path or item.a_path
            if path is None:
                continue

            if item.deleted_file:
                status = "deleted"
            elif item.new_file:
                status = "added"
            elif item.renamed:
                status = "renamed"
            else:
                status = "modified"

            changes.append(
                FileChange(
                    path=path,
                    status=status,
                    old_path=item.a_path if item.renamed else None,
                )
            )

        # Untracked files.
        for path in repo.untracked_files:
            changes.append(FileChange(path=path, status="added"))

    else:
        # Validate the base revision and compare it with HEAD.
        try:
            base_commit = repo.commit(base)
        except Exception as exc:
            raise ValueError(f"Invalid base revision: {base}") from exc

        diff = base_commit.diff(repo.head.commit, find_renames=True)

        for item in diff:
            if item.deleted_file:
                path = item.a_path
                status = "deleted"
            elif item.renamed:
                path = item.b_path
                status = "renamed"
            elif item.new_file:
                path = item.b_path
                status = "added"
            else:
                path = item.b_path
                status = "modified"

            if path is not None:
                changes.append(
                    FileChange(
                        path=path,
                        status=status,
                        old_path=item.a_path if item.renamed else None,
                    )
                )

    # Deduplicate and return deterministic results.
    unique: dict[tuple[str, str], FileChange] = {}
    for change in changes:
        unique[(change.path, change.status)] = change

    return sorted(unique.values(), key=lambda change: change.path)
