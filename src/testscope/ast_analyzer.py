"""Extract import dependencies from Python source files."""

import ast
from pathlib import Path


def extract_imports(file_path: str | Path) -> set[str]:
    """Return module names imported by a Python file."""
    path = Path(file_path)

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            relative_prefix = "." * node.level

            if node.module:
                imports.add(f"{relative_prefix}{node.module}")
            elif node.level:
                imports.add(relative_prefix)

    return imports
