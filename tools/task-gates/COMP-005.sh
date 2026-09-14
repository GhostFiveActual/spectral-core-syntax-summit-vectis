#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "============================================================"
echo " VECTIS // COMP-005 // DIAGNOSTIC ACCEPTANCE"
echo "============================================================"

required=(
    src/vectis/diagnostic.py
    src/vectis/lexer.py
    src/vectis/parser.py
    tests/test_diagnostic.py
    docs/design/diagnostics.md
)

for file in "${required[@]}"; do
    if [[ ! -s "$file" ]]; then
        echo "ERROR: missing required COMP-005 artifact: $file"
        exit 1
    fi
done

echo
echo "[1/8] Compile diagnostic integration..."
python3 -m py_compile \
    src/vectis/diagnostic.py \
    src/vectis/lexer.py \
    src/vectis/parser.py \
    tests/test_diagnostic.py

echo
echo "[2/8] Stable API, severity levels, source spans, machine form..."
PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
import json

from vectis.diagnostic import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticError,
    DiagnosticSeverity,
)
from vectis.source_position import SourcePosition
from vectis.source_span import SourceSpan

expected_codes = {
    "LEX001",
    "LEX002",
    "LEX003",
    "SYN001",
    "SYN002",
    "SYN003",
    "SYN004",
    "SYN005",
    "SYN006",
    "SYN007",
}

if {item.value for item in DiagnosticCode} != expected_codes:
    raise SystemExit("ERROR: stable diagnostic code registry mismatch")

if {item.value for item in DiagnosticSeverity} != {"error", "warning"}:
    raise SystemExit("ERROR: severity registry mismatch")

span = SourceSpan(
    start=SourcePosition(line=2, column=3, file="gate.vectis"),
    end=SourcePosition(line=2, column=7, file="gate.vectis"),
)

diagnostic = Diagnostic(
    code=DiagnosticCode.SYN_EXPECTED_TOKEN,
    severity=DiagnosticSeverity.ERROR,
    message="expected ';'",
    span=span,
)

payload = diagnostic.to_dict()
json.dumps(payload)

if payload != {
    "code": "SYN003",
    "severity": "error",
    "message": "expected ';'",
    "source": {
        "file": "gate.vectis",
        "start": {"line": 2, "column": 3},
        "end": {"line": 2, "column": 7},
    },
}:
    raise SystemExit("ERROR: machine-readable diagnostic shape mismatch")

error = DiagnosticError(diagnostic)

if error.code != "SYN003" or error.severity != "error":
    raise SystemExit("ERROR: exception compatibility fields mismatch")

if error.span is not span:
    raise SystemExit("ERROR: exception lost canonical SourceSpan")

if "gate.vectis:2:3:" not in str(error):
    raise SystemExit("ERROR: readable diagnostic prefix mismatch")

print("shared diagnostic API: PASS")
PY

echo
echo "[3/8] Lexer diagnostic integration..."
PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from vectis.lexer import Lexer, LexerError
from vectis.source_span import SourceSpan

cases = (
    ('"unterminated', "LEX001"),
    ("<", "LEX002"),
    ("@", "LEX003"),
)

for source, expected in cases:
    try:
        Lexer(source, file="lexer-gate.vectis").tokenize()
    except LexerError as exc:
        if exc.code != expected:
            raise SystemExit(
                f"ERROR: {source!r}: expected {expected}, got {exc.code}"
            )
        if exc.severity != "error":
            raise SystemExit("ERROR: lexer severity mismatch")
        if not isinstance(exc.span, SourceSpan):
            raise SystemExit("ERROR: lexer diagnostic has no SourceSpan")
        if exc.to_dict()["source"]["file"] != "lexer-gate.vectis":
            raise SystemExit("ERROR: lexer diagnostic lost source file")
    else:
        raise SystemExit(f"ERROR: expected LexerError for {source!r}")

print("lexer diagnostics: PASS")
PY

echo
echo "[4/8] Parser diagnostic integration..."
PYTHONPATH="${PYTHONPATH:-}:src" python3 - <<'PY'
from vectis.parser import ParserError, parse
from vectis.source_span import SourceSpan

cases = (
    ("otherwise { publish result; }", "SYN002"),
    ("publish ;", "SYN004"),
    ("publish result", "SYN003"),
    ('mission "x" { publish result;', "SYN005"),
    ("citations [a,];", "SYN006"),
    ("not_a_statement", "SYN001"),
    ("report", "SYN007"),
)

for source, expected in cases:
    try:
        parse(source, file="parser-gate.vectis")
    except ParserError as exc:
        if exc.code != expected:
            raise SystemExit(
                f"ERROR: {source!r}: expected {expected}, got {exc.code}"
            )
        if exc.severity != "error":
            raise SystemExit("ERROR: parser severity mismatch")
        if not isinstance(exc.span, SourceSpan):
            raise SystemExit("ERROR: parser diagnostic has no SourceSpan")
        if exc.to_dict()["source"]["file"] != "parser-gate.vectis":
            raise SystemExit("ERROR: parser diagnostic lost source file")
    else:
        raise SystemExit(f"ERROR: expected ParserError for {source!r}")

print("parser diagnostics: PASS")
PY

echo
echo "[5/8] Dedicated diagnostic tests..."
PYTHONPATH="${PYTHONPATH:-}:src" \
    python3 -m unittest -v tests.test_diagnostic

echo
echo "[6/8] Existing lexer/parser regression suites..."
PYTHONPATH="${PYTHONPATH:-}:src" \
    python3 -m unittest -v tests.test_lexer tests.test_parser

echo
echo "[7/8] COMP-004 parser contract remains green..."
bash tools/task-gates/COMP-004.sh

echo
echo "[8/8] Diagnostic design contract..."
python3 - <<'PY'
from pathlib import Path

text = Path("docs/design/diagnostics.md").read_text(
    encoding="utf-8"
).lower()

required = (
    "stable diagnostic code",
    "severity",
    "source span",
    "machine-readable",
    "lex001",
    "lex002",
    "lex003",
    "syn001",
    "syn002",
    "syn003",
    "syn004",
    "syn005",
    "syn006",
    "syn007",
    "lexererror",
    "parsererror",
)

missing = [item for item in required if item not in text]

if missing:
    raise SystemExit(
        "ERROR: diagnostic design contract missing: "
        + ", ".join(missing)
    )

print("diagnostic design contract: PASS")
PY

echo "============================================================"
echo " COMP-005 DIAGNOSTIC ACCEPTANCE PASSED"
echo "============================================================"
