#!/usr/bin/env python3
from __future__ import annotations

# BEGIN VECTIS TASK-GATE PYTHONPATH BOOTSTRAP
#
# acceptance.py runs from a src-layout repository. Some acceptance checks
# spawn a fresh Python interpreter, so modifying only this process's
# sys.path is insufficient. Keep the current interpreter and every child
# Python process pointed at the canonical project package.
import os as _vectis_gate_os
import pathlib as _vectis_gate_pathlib
import sys as _vectis_gate_sys

_VECTIS_GATE_ROOT = (
    _vectis_gate_pathlib.Path(__file__)
    .resolve()
    .parents[2]
)

_VECTIS_GATE_SRC = (
    _VECTIS_GATE_ROOT
    / "src"
)

for _vectis_gate_entry in (
    str(_VECTIS_GATE_ROOT),
    str(_VECTIS_GATE_SRC),
):
    if (
        _vectis_gate_entry
        not in _vectis_gate_sys.path
    ):
        _vectis_gate_sys.path.insert(
            0,
            _vectis_gate_entry,
        )

_vectis_gate_existing_pythonpath = (
    _vectis_gate_os.environ.get(
        "PYTHONPATH",
        "",
    )
)

_vectis_gate_pythonpath = [
    str(_VECTIS_GATE_SRC),
    str(_VECTIS_GATE_ROOT),
]

if _vectis_gate_existing_pythonpath:
    _vectis_gate_pythonpath.append(
        _vectis_gate_existing_pythonpath
    )

_vectis_gate_os.environ[
    "PYTHONPATH"
] = _vectis_gate_os.pathsep.join(
    _vectis_gate_pythonpath
)
# END VECTIS TASK-GATE PYTHONPATH BOOTSTRAP


import importlib
import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = json.loads(
    (ROOT / "competition/task-contracts.json").read_text(
        encoding="utf-8"
    )
)["tasks"]


def fail(message: str) -> None:
    raise SystemExit("ERROR: " + message)


def backlog() -> dict[str, dict]:
    data = json.loads(
        (ROOT / "competition/backlog.json").read_text(
            encoding="utf-8"
        )
    )
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    return {item["id"]: item for item in tasks}


def run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        fail(
            "command failed "
            + str(result.returncode)
            + ": "
            + " ".join(command)
        )


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: acceptance.py TASK-ID")

    task_id = sys.argv[1]
    spec = TASKS.get(task_id)

    if spec is None:
        fail(f"no unattended acceptance spec for {task_id}")

    records = backlog()

    if task_id not in records:
        fail(f"{task_id} is not present in backlog")

    print("=" * 64)
    print(f" VECTIS // {task_id} // UNATTENDED ACCEPTANCE")
    print("=" * 64)

    print("\n[1/8] Predecessors...")
    for predecessor in spec.get("predecessors", []):
        record = records.get(predecessor)
        if not record or record.get("status") != "done":
            fail(f"predecessor {predecessor} is not done")
        print(f"{predecessor}: DONE")

    print("\n[2/8] Required artifacts...")
    for relative in spec["required_files"]:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing required artifact: {relative}")
        print(f"{relative}: PRESENT")

    print("\n[3/8] Python compilation...")
    for relative in spec["files"]:
        if not relative.endswith(".py"):
            continue
        path = ROOT / relative
        if path.is_file():
            py_compile.compile(str(path), doraise=True)
            print(f"{relative}: COMPILES")

    print("\n[4/8] Stable public symbols...")
    sys.path.insert(0, str(ROOT / "src"))
    for module_name, symbols in spec.get("python_symbols", {}).items():
        module = importlib.import_module(module_name)
        for symbol in symbols:
            if not hasattr(module, symbol):
                fail(f"{module_name} missing symbol {symbol}")
            print(f"{module_name}.{symbol}: PRESENT")

    print("\n[5/8] Independent documentation concepts...")
    doc_file = spec.get("doc_file")
    if doc_file:
        text = (ROOT / doc_file).read_text(
            encoding="utf-8"
        ).lower()
        for term in spec.get("doc_terms", []):
            if term.lower() not in text:
                fail(f"{doc_file} missing concept {term!r}")
        print(f"{doc_file}: CONTRACT TERMS PASS")

    print("\n[6/8] Minimum meaningful test surface...")
    test_file = ROOT / spec["test_file"]
    text = test_file.read_text(encoding="utf-8")
    count = len(
        re.findall(
            r"(?m)^\s*def\s+test_[A-Za-z0-9_]+\s*\(",
            text,
        )
    )
    minimum = int(spec.get("min_tests", 1))
    if count < minimum:
        fail(
            f"{spec['test_file']} has {count} tests; "
            f"minimum is {minimum}"
        )
    print(f"{spec['test_file']}: {count} tests >= {minimum}")

    print("\n[7/8] Task-specific test module...")
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            spec["test_module"],
        ]
    )

    print("\n[8/8] Complete repository quality gate...")
    run(["bash", "tools/quality-gate.sh"])

    print("=" * 64)
    print(f" {task_id} UNATTENDED ACCEPTANCE PASSED")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
