#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "usage: $0 TASK-ID" >&2
    exit 2
fi

TASK_ID="$1"

ROOT="$(
    cd "$(
        dirname "${BASH_SOURCE[0]}"
    )/../.." &&
    pwd
)"

GATE="$ROOT/tools/task-gates/${TASK_ID}.sh"

if [ ! -f "$GATE" ]; then
    echo "task gate: none for $TASK_ID"
    exit 0
fi

if [ ! -x "$GATE" ]; then
    echo \
        "ERROR: task gate is not executable: $GATE" \
        >&2
    exit 2
fi

echo "============================================================"
echo " VECTIS // TASK GATE // $TASK_ID"
echo "============================================================"

exec "$GATE"
