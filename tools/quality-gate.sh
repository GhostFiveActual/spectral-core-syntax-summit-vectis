#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src"

echo "============================================================"
echo " VECTIS // QUALITY GATE"
echo "============================================================"

echo
echo "[1/7] Python compilation..."
python3 -m compileall -q src tests tools

echo
echo "[2/7] Unit tests..."
python3 -m unittest discover \
    -s tests \
    -p 'test_*.py' \
    -v

echo
echo "[3/7] Package import..."
python3 - <<'PY'
import vectis
from vectis.cli import build_parser

assert vectis.__version__
assert build_parser().prog == "vectis"

print("package import: PASS")
PY

echo
echo "[4/7] Protected project records..."

test -f competition/manifest.md
test -f competition/provenance.md
test -f competition/autonomy-policy.md
test -f competition/backlog.json
test -f competition/roles.json

echo "protected records: PRESENT"

echo
echo "[5/7] Repository whitespace validation..."
git diff --check

echo
echo "[6/7] Secret-pattern scan..."

if grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.autonomy \
    --exclude='*.log' \
    '(BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})' \
    .; then
    echo "Potential secret material detected."
    exit 1
fi

echo "secret-pattern scan: PASS"

echo
echo "[7/7] Repository boundary scan..."

if find . \
    -type l \
    -not -path './.git/*' \
    -print \
    | grep -q .; then
    echo "Symbolic links are prohibited in the autonomous repository."
    exit 1
fi

echo "repository boundary scan: PASS"

echo
echo "============================================================"
echo " VECTIS // QUALITY GATE PASSED"
echo "============================================================"
