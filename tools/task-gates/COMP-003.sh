#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " VECTIS // TASK GATE // COMP-003"
echo "============================================================"

echo "[1/7] Required AST artifacts..."

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

echo "[2/7] Canonical compiler primitive ownership..."

if grep -Eq \
    '^[[:space:]]*class[[:space:]]+(SourcePosition|SourceSpan|Token|Lexer)\b' \
    src/vectis/ast.py
then
    echo "ERROR: AST redefines completed compiler primitives."
    exit 1
fi

grep -q \
    'from vectis.source_span import SourceSpan' \
    src/vectis/ast.py

echo "[3/7] Required typed AST surface..."

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from dataclasses import is_dataclass

import vectis.ast as ast
from vectis.source_span import SourceSpan

required = (
    "Node",
    "Expression",
    "Statement",
    "Program",
    "Block",
    "StringLiteral",
    "NumberLiteral",
    "BooleanLiteral",
    "Reference",
    "UnaryExpression",
    "BinaryExpression",
    "Mission",
    "SourceDeclaration",
    "AnalyzeDeclaration",
    "RequireStatement",
    "RequestStatement",
    "PublishStatement",
    "CitationsStatement",
    "ConfidenceStatement",
    "WhenStatement",
)

for name in required:
    value = getattr(ast, name, None)

    if value is None:
        raise SystemExit(
            f"ERROR: missing AST type {name}"
        )

    if not is_dataclass(value):
        raise SystemExit(
            f"ERROR: {name} is not a dataclass"
        )

annotations = ast.Node.__dataclass_fields__

if "span" not in annotations:
    raise SystemExit(
        "ERROR: Node does not retain source span"
    )

print("typed AST surface: PASS")
print("canonical SourceSpan:", SourceSpan)
PY

echo "[4/7] AST-focused unit tests..."

PYTHONPATH="${PYTHONPATH:-}:src" \
python3 -m unittest \
    -v \
    tests.test_ast

echo "[5/7] Invariant documentation contract..."

for phrase in \
    "Canonical source locations" \
    "Immutability" \
    "Node categories" \
    "Structural typing" \
    "Grammar boundary"
do
    grep -q "$phrase" \
        docs/design/ast-invariants.md || {
        echo "ERROR: AST invariant section missing: $phrase"
        exit 1
    }
done

echo "[6/7] Completed compiler primitives remain canonical..."

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from vectis.ast import Node
from vectis.lexer import Lexer
from vectis.source_position import SourcePosition
from vectis.source_span import SourceSpan
from vectis.token import Token

position = SourcePosition(
    line=1,
    column=1,
    file="gate.vectis",
)

span = SourceSpan(
    start=position,
    end=position,
)

node = Node(
    span=span,
)

assert type(node.span) is SourceSpan

tokens = Lexer(
    'mission demo {}',
    file='gate.vectis',
).tokenize()

assert tokens
assert all(
    type(token) is Token
    for token in tokens
)

print("completed compiler primitives: PASS")
PY

echo "[7/7] AST module does not import future parser/runtime layers..."

if grep -Eq \
    'vectis\.(parser|semantic|runtime|execution|graph)' \
    src/vectis/ast.py
then
    echo "ERROR: AST depends on a future compiler/runtime layer."
    exit 1
fi

echo "============================================================"
echo " COMP-003 TASK GATE PASSED"
echo "============================================================"
