#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " VECTIS // CONTRACT GATE // NORMATIVE GRAMMAR"
echo "============================================================"

required=(
    docs/spec/grammar.md
    docs/spec/lexical-spec.md
    docs/design/ast-invariants.md
    examples/README.md
    examples/valid/research-accessibility.vectis
    examples/valid/expression-precedence.vectis
    examples/valid/citations.vectis
    examples/valid/booleans.vectis
    examples/invalid/missing-semicolon.vectis
    examples/invalid/standalone-otherwise.vectis
    examples/invalid/missing-expression.vectis
    examples/invalid/unclosed-block.vectis
)

for file in "${required[@]}"; do
    if [[ ! -s "$file" ]]; then
        echo "ERROR: missing required grammar artifact: $file"
        exit 1
    fi
done

python3 - <<'PY'
from pathlib import Path

grammar = Path(
    "docs/spec/grammar.md"
).read_text(encoding="utf-8")

required_fragments = [
    "Status: normative.",
    "mission_statement",
    "source_statement",
    "analyze_statement",
    "require_statement",
    "request_statement",
    "publish_statement",
    "citations_statement",
    "confidence_statement",
    "when_statement",
    "logical_or",
    "logical_and",
    "equality",
    "comparison",
    "additive",
    "multiplicative",
    "unary",
    "primary",
    "SourceDeclaration",
    "AnalyzeDeclaration",
    "WhenStatement",
    "BinaryExpression",
    "UnaryExpression",
    "SourceSpan",
]

missing = [
    item
    for item in required_fragments
    if item not in grammar
]

if missing:
    raise SystemExit(
        "ERROR: grammar contract missing:\n"
        + "\n".join(missing)
    )

for forbidden in (
    'Exponentiation `**`',
    '"**"',
    "function-call expressions are supported",
):
    if forbidden in grammar:
        raise SystemExit(
            f"ERROR: unsupported grammar feature present: {forbidden}"
        )

draft = Path(
    "docs/spec/syntax-draft.md"
).read_text(encoding="utf-8")

if "Status: historical and non-normative." not in draft:
    raise SystemExit(
        "ERROR: syntax draft still appears authoritative"
    )

print("normative grammar structure: PASS")
PY

echo
echo "[lexer compatibility]"

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from pathlib import Path

from vectis.lexer import Lexer

for path in sorted(
    Path("examples/valid").glob("*.vectis")
):
    tokens = Lexer(
        path.read_text(encoding="utf-8"),
        file=str(path),
    ).tokenize()

    if not tokens:
        raise SystemExit(
            f"ERROR: valid example produced no tokens: {path}"
        )

    print(
        f"{path}: {len(tokens)} tokens PASS"
    )

print("all valid examples lexically conform: PASS")
PY

echo
echo "[canonical AST surface]"

PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
import vectis.ast as ast

required = {
    "Program",
    "Block",
    "Mission",
    "SourceDeclaration",
    "AnalyzeDeclaration",
    "RequireStatement",
    "RequestStatement",
    "PublishStatement",
    "CitationsStatement",
    "ConfidenceStatement",
    "WhenStatement",
    "StringLiteral",
    "NumberLiteral",
    "BooleanLiteral",
    "Reference",
    "UnaryExpression",
    "BinaryExpression",
}

missing = sorted(
    required - set(vars(ast))
)

if missing:
    raise SystemExit(
        "ERROR: grammar references unavailable AST nodes:\n"
        + "\n".join(missing)
    )

print("grammar -> canonical AST surface: PASS")
PY

echo "============================================================"
echo " NORMATIVE GRAMMAR CONTRACT PASSED"
echo "============================================================"
