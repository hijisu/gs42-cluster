"""domain 계층은 Django/DRF를 import하지 않는다 (AGENTS.md)."""

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
FORBIDDEN = ("django", "rest_framework")


def test_domain_layers_do_not_import_django():
    violations = []
    for path in BACKEND.glob("*/domain/**/*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".")[0] in FORBIDDEN:
                    violations.append(f"{path.relative_to(BACKEND)}: {name}")
    assert not violations, violations
