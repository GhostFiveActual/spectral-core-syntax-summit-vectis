from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "competition" / "task-contracts.json"

_manifest = json.loads(
    MANIFEST_PATH.read_text(encoding="utf-8")
)
TASK_SPECS = _manifest["tasks"]

TASK_FILE_RULES = {
    task_id: set(spec["files"])
    for task_id, spec in TASK_SPECS.items()
}

TASK_FILE_RULES.update(
    {
        "COMP-003": {
            "src/vectis/ast.py",
            "tests/test_ast.py",
            "docs/design/ast-invariants.md",
        },
        "COMP-004": {
            "src/vectis/parser.py",
            "tests/test_parser.py",
            "docs/design/parser.md",
        },
        "COMP-005": {
            "src/vectis/diagnostic.py",
            "src/vectis/lexer.py",
            "src/vectis/parser.py",
            "tests/test_diagnostic.py",
            "docs/design/diagnostics.md",
        },
    }
)
