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
echo "[3/8] Package import..."

python3 - <<'PYIMPORT'
import vectis
print("package import: PASS")
PYIMPORT

echo
echo "[4/8] Runtime import of all VECTIS modules..."

python3 - <<'PYIMPORTALL'
import importlib
import pkgutil
import vectis

failures = []

for module in pkgutil.walk_packages(
    vectis.__path__,
    prefix=vectis.__name__ + ".",
):
    name = module.name

    try:
        importlib.import_module(name)
        print("import:", name, "PASS")
    except Exception as exc:
        failures.append(
            f"{name}: {type(exc).__name__}: {exc}"
        )

if failures:
    print()
    print("runtime module import failures:")
    for failure in failures:
        print(" -", failure)
    raise SystemExit(1)

print("runtime module imports: PASS")
PYIMPORTALL

echo "[5/8] Protected project records..."

test -f competition/manifest.md
test -f competition/provenance.md
test -f competition/autonomy-policy.md
test -f competition/backlog.json
test -f competition/roles.json

echo "protected records: PRESENT"

echo
echo "[6/8] Repository whitespace validation..."
git diff --check

echo
echo "[7/8] Secret-pattern scan..."

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
echo "[8/8] Repository boundary scan..."

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
