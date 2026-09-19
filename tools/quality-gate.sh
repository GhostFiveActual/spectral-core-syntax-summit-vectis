#!/usr/bin/env bash
# GHOST FIVE // SPECTRAL CORE // VECTIS
# Runs the full Spectral Core quality gate for VECTIS before merge or release.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src"

echo "============================================================"
echo " GHOST FIVE // SPECTRAL CORE // VECTIS"
echo " QUALITY GATE"
echo "============================================================"

echo
echo "[1/9] Python compilation..."
python3 -m compileall -q src tests tools

echo
echo "[2/9] Unit tests..."
python3 -m unittest discover \
    -s tests \
    -p 'test_*.py' \
    -v

echo
echo "[3/9] Package import..."
python3 - <<'PYIMPORT'
import vectis
print("package import:", vectis.__version__, "PASS")
PYIMPORT

echo
echo "[4/9] Runtime import of all VECTIS modules..."
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
    print("runtime module import failures:")
    for failure in failures:
        print("ERROR:", failure)
    raise SystemExit(1)

print("runtime module imports: PASS")
PYIMPORTALL

echo
echo "[5/9] Public repository boundary..."
for path in \
    .autonomy \
    artifacts \
    competition \
    docs/submission \
    tools/spectral_core_controller.py \
    tools/vectis_task_contracts.py \
    tools/task-gates; do
    if [[ -e "$path" ]]; then
        echo "ERROR: internal path must not ship in public product tree: $path"
        exit 1
    fi
done
echo "public repository boundary: PASS"

echo
echo "[6/9] Repository whitespace validation..."
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git diff --check
else
    python3 - <<'PYSPACE'
from pathlib import Path

bad = []
suffixes = {
    ".py",
    ".md",
    ".sh",
    ".vectis",
    ".html",
    ".css",
    ".js",
    ".yml",
    ".yaml",
    ".toml",
}

for root in (
    Path("src"),
    Path("tests"),
    Path("tools"),
    Path("docs"),
    Path("examples"),
):
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            1,
        ):
            if line.endswith((" ", "\t")):
                bad.append(
                    f"{path}:{number}: trailing whitespace"
                )

if bad:
    print("\n".join(bad))
    raise SystemExit(1)
PYSPACE
fi
echo "whitespace validation: PASS"

echo
echo "[7/9] Secret pattern scan..."
if grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=build \
    --exclude-dir=dist \
    --exclude='*.log' \
    '(BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})' \
    .; then
    echo "ERROR: potential secret material detected."
    exit 1
fi
echo "secret pattern scan: PASS"

echo
echo "[8/9] Symlink boundary scan..."
if find . \
    -path './.git' -prune -o \
    -path './.venv' -prune -o \
    -path './venv' -prune -o \
    -path './build' -prune -o \
    -path './dist' -prune -o \
    -type l -print \
    | grep -q .; then
    echo "ERROR: unexpected symbolic link found in product repository."
    exit 1
fi
echo "symlink boundary scan: PASS"

echo
echo "[9/9] Ghost Five repository policy..."
python3 tools/repository-policy.py

echo
echo "============================================================"
echo " GHOST FIVE // SPECTRAL CORE // VECTIS"
echo " QUALITY GATE PASSED"
echo "============================================================"
