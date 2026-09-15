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

# Every contracted task must remain represented exactly once and in the
# authoritative matrix order. Completing a task changes its status; it must
# never remove, duplicate, or reorder the task in the backlog.
contracted = [
    item
    for item in tasks
    if item.get("id") in TASK_SPECS
]
contracted_ids = [
    item["id"]
    for item in contracted
]

if contracted_ids != expected:
    raise SystemExit(
        "ERROR: contracted backlog order does not match matrix.\n"
        f"backlog={contracted_ids}\n"
        f"matrix={expected}"
    )

# Contracted work advances monotonically. Completed tasks must form one
# contiguous prefix and every unfinished contracted task must form the
# remaining contiguous suffix. This rejects skipped or out-of-order
# completion while allowing the matrix to shrink naturally as work finishes.
seen_unfinished = False

for item in contracted:
    task_id = item["id"]
    status = item.get("status")

    if status == "done":
        if seen_unfinished:
            raise SystemExit(
                "ERROR: completed contracted task appears after "
                "unfinished contracted work.\n"
                f"task={task_id}\n"
                f"status={status!r}"
            )
    else:
        seen_unfinished = True

contracted_pending = [
    item["id"]
    for item in contracted
    if item.get("status") != "done"
]

if contracted_pending:
    first_pending_index = expected.index(
        contracted_pending[0]
    )
    expected_pending = expected[
        first_pending_index:
    ]
else:
    expected_pending = []

if contracted_pending != expected_pending:
    raise SystemExit(
        "ERROR: pending contracted tasks are not the "
        "remaining matrix suffix.\n"
        f"pending={contracted_pending}\n"
        f"expected_suffix={expected_pending}\n"
        f"matrix={expected}"
    )

# Preserve the original fail-closed behavior for any non-done backlog task
# that is outside the contracted unattended matrix.
if pending != contracted_pending:
    unexpected_pending = [
        task_id
        for task_id in pending
        if task_id not in TASK_SPECS
    ]

    raise SystemExit(
        "ERROR: pending backlog contains work outside the "
        "contracted unattended matrix.\n"
        f"unexpected={unexpected_pending}\n"
        f"pending={pending}"
    )

completed_prefix = expected[
    :len(expected) - len(contracted_pending)
]

for task_id in contracted_pending:
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
    "unattended matrix: PASS // "
    f"{len(contracted_pending)} pending tasks contracted"
)
print(
    "completed prefix =",
    completed_prefix,
)

if contracted_pending:
    print(
        "first pending =",
        contracted_pending[0],
    )
    print(
        "final task    =",
        contracted_pending[-1],
    )
else:
    print("first pending = NONE")
    print("final task    = NONE")
    print("all contracted unattended tasks = COMPLETE")
PY
