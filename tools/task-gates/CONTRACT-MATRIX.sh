#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHONPATH="$ROOT/tools:${PYTHONPATH:-}" python3 - <<'PY'
import json
import os
from pathlib import Path

from vectis_task_contracts import TASK_FILE_RULES, TASK_SPECS

root = Path.cwd()
data = json.loads(
    (root / "competition/backlog.json").read_text(
        encoding="utf-8"
    )
)
tasks = data if isinstance(data, list) else data.get("tasks", [])

pending = [
    item["id"]
    for item in tasks
    if item.get("status") != "done"
]
expected = list(TASK_SPECS)

if pending != expected:
    raise SystemExit(
        "ERROR: pending backlog order does not match matrix.\n"
        f"pending={pending}\n"
        f"matrix={expected}"
    )

for task_id in pending:
    allowed = TASK_FILE_RULES.get(task_id)
    if not allowed:
        raise SystemExit(
            f"ERROR: {task_id} has no file boundary"
        )

    gate = root / "tools/task-gates" / f"{task_id}.sh"
    if not gate.is_file() or not os.access(gate, os.X_OK):
        raise SystemExit(
            f"ERROR: {task_id} gate missing or not executable"
        )

    spec = TASK_SPECS[task_id]
    if not set(spec["required_files"]) <= set(allowed):
        raise SystemExit(
            f"ERROR: {task_id} required artifacts escape boundary"
        )

    if spec["test_file"] not in allowed:
        raise SystemExit(
            f"ERROR: {task_id} test file escapes boundary"
        )

print(
    f"unattended matrix: PASS // {len(pending)} pending tasks contracted"
)
print("first pending =", pending[0])
print("final task    =", pending[-1])
PY
