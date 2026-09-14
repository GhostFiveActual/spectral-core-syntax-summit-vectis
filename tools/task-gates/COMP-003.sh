#!/usr/bin/env bash
set -euo pipefail

ROOT="$(
    cd "$(
        dirname "${BASH_SOURCE[0]}"
    )/../.." &&
    pwd
)"

cd "$ROOT"

export PYTHONPATH="$ROOT/src"

echo "[1/6] Required AST artifacts..."

for file in \
    src/vectis/ast.py \
    tests/test_ast.py \
    docs/design/ast-invariants.md
do
    if [ ! -s "$file" ]; then
        echo "ERROR: missing/non-empty artifact: $file"
        exit 1
    fi
done

echo "required artifacts: PASS"

echo
echo "[2/6] AST module compilation/import..."

python3 -m py_compile \
    src/vectis/ast.py \
    tests/test_ast.py

python3 - <<'PY'
import vectis.ast

print(
    "vectis.ast import:",
    vectis.ast.__file__,
)
PY

echo
echo "[3/6] AST contract structure..."

python3 - <<'PY'
import inspect

import vectis.ast as ast
from vectis.source_span import SourceSpan


classes = {
    name: cls
    for name, cls in inspect.getmembers(
        ast,
        inspect.isclass,
    )
    if cls.__module__ == ast.__name__
}

if not classes:
    raise SystemExit(
        "ERROR: vectis.ast defines no AST classes"
    )

span_nodes = []

for name, cls in classes.items():
    annotations = {}

    for base in reversed(cls.__mro__):
        annotations.update(
            getattr(
                base,
                "__annotations__",
                {},
            )
        )

    if "span" in annotations:
        span_nodes.append(name)

if not span_nodes:
    raise SystemExit(
        "ERROR: no AST node declares a span field"
    )

print(
    "AST classes:",
    ", ".join(sorted(classes)),
)

print(
    "span-bearing AST classes:",
    ", ".join(sorted(span_nodes)),
)

print(
    "canonical span type:",
    SourceSpan,
)
PY

echo
echo "[4/6] AST unit tests..."

python3 -m unittest -v \
    tests.test_ast

echo
echo "[5/6] Invariant documentation contract..."

python3 - <<'PY'
from pathlib import Path

path = Path(
    "docs/design/ast-invariants.md"
)

text = path.read_text(
    encoding="utf-8"
).lower()

required_concepts = {
    "source span": (
        "source span",
        "sourcespan",
    ),
    "invariant": (
        "invariant",
        "invariants",
    ),
    "typed": (
        "typed",
        "type",
    ),
    "immutability or mutation policy": (
        "immutable",
        "immutability",
        "mutation",
        "mutable",
    ),
}

missing = []

for label, variants in required_concepts.items():
    if not any(
        variant in text
        for variant in variants
    ):
        missing.append(label)

if missing:
    raise SystemExit(
        "ERROR: AST invariant documentation "
        "missing concepts: "
        + ", ".join(missing)
    )

print(
    "AST invariant documentation: PASS"
)
PY

echo
echo "[6/6] Completed compiler dependency protection..."

python3 - <<'PY'
from vectis.source_position import SourcePosition
from vectis.source_span import SourceSpan
from vectis.token import Token
from vectis.lexer import Lexer

position = SourcePosition(
    line=1,
    column=1,
    file="gate.vectis",
)

span = SourceSpan(
    start=position,
    end=position,
)

token = Token(
    type="identifier",
    value="x",
    span=span,
)

lexed = Lexer(
    "mission",
    file="gate.vectis",
).tokenize()

assert token.span is span
assert lexed
assert isinstance(
    lexed[0],
    Token,
)

print(
    "COMP-001/COMP-002 dependencies: PASS"
)
PY

echo
echo "============================================================"
echo " COMP-003 // TASK GATE PASSED"
echo "============================================================"
