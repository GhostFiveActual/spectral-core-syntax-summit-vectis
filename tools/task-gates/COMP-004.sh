#!/usr/bin/env bash
set -euo pipefail

ROOT="$(
    cd "$(
        dirname "${BASH_SOURCE[0]}"
    )/../.." &&
    pwd
)"

cd "$ROOT"

echo "============================================================"
echo " VECTIS // COMP-004 // PARSER ACCEPTANCE"
echo "============================================================"

required=(
    src/vectis/parser.py
    tests/test_parser.py
    docs/design/parser.md
    docs/spec/grammar.md
    tools/task-gates/GRAMMAR.sh
)

for file in "${required[@]}"; do
    if [[ ! -s "$file" ]]; then
        echo "ERROR: missing required COMP-004 artifact: $file"
        exit 1
    fi
done

echo
echo "[1/7] Normative grammar remains green..."
bash tools/task-gates/GRAMMAR.sh

echo
echo "[2/7] Parser and parser tests compile..."
python3 -m py_compile \
    src/vectis/parser.py \
    tests/test_parser.py

echo
echo "[3/7] Canonical parser API and AST dependency..."

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
import inspect

import vectis.parser as parser
from vectis.ast import Program

if not hasattr(parser, "parse"):
    raise SystemExit(
        "ERROR: vectis.parser must expose parse(source, file=...)."
    )

if not callable(parser.parse):
    raise SystemExit(
        "ERROR: vectis.parser.parse is not callable."
    )

sig = inspect.signature(parser.parse)
params = sig.parameters

if "source" not in params:
    raise SystemExit(
        "ERROR: parse() must expose a source parameter."
    )

if "file" not in params:
    raise SystemExit(
        "ERROR: parse() must expose a file parameter."
    )

program = parser.parse(
    "",
    file="<comp004-empty>",
)

if not isinstance(program, Program):
    raise SystemExit(
        "ERROR: parse() must return canonical vectis.ast.Program."
    )

if program.statements != ():
    raise SystemExit(
        "ERROR: empty source must produce an empty Program."
    )

print("canonical parse(source, file=...) API: PASS")
PY

echo
echo "[4/7] Official valid examples parse..."

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from pathlib import Path

from vectis.ast import Program
from vectis.parser import parse

for path in sorted(
    Path("examples/valid").glob("*.vectis")
):
    program = parse(
        path.read_text(encoding="utf-8"),
        file=str(path),
    )

    if not isinstance(program, Program):
        raise SystemExit(
            f"ERROR: {path} did not produce Program"
        )

    print(f"{path}: PASS")

print("all official valid examples: PASS")
PY

echo
echo "[5/7] Official invalid examples are rejected..."

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from pathlib import Path

from vectis.parser import parse

for path in sorted(
    Path("examples/invalid").glob("*.vectis")
):
    source = path.read_text(encoding="utf-8")

    try:
        parse(
            source,
            file=str(path),
        )
    except Exception as exc:
        message = str(exc)

        if not message.strip():
            raise SystemExit(
                f"ERROR: {path} raised an empty diagnostic"
            )

        if str(path) not in message:
            raise SystemExit(
                f"ERROR: {path} diagnostic lacks source file: {message}"
            )

        print(
            f"{path}: rejected PASS // "
            f"{type(exc).__name__}: {message[:180]}"
        )
    else:
        raise SystemExit(
            f"ERROR: invalid example parsed successfully: {path}"
        )

print("all official invalid examples: PASS")
PY

echo
echo "[6/7] Parser conformance test suite..."

PYTHONPATH="${PYTHONPATH:-}:src" \
    python3 -m unittest -v tests.test_parser

echo
echo "[7/7] Parser design contract..."

python3 - <<'PY'
from pathlib import Path

text = Path(
    "docs/design/parser.md"
).read_text(encoding="utf-8").lower()

required = (
    "grammar",
    "precedence",
    "associativ",
    "source span",
    "diagnostic",
    "parse(",
    "canonical ast",
)

missing = [
    item
    for item in required
    if item not in text
]

if missing:
    raise SystemExit(
        "ERROR: parser design contract missing concepts: "
        + ", ".join(missing)
    )

print("parser design contract: PASS")
PY

echo
echo "============================================================"
echo " COMP-004 PARSER ACCEPTANCE PASSED"
echo "============================================================"
