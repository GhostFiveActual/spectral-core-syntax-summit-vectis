#!/usr/bin/env python3
# GHOST FIVE // SPECTRAL CORE // VECTIS
# Enforces repository branding, writing, comment, and public product standards.

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BRAND = "GHOST FIVE // SPECTRAL CORE // VECTIS"
SKIP_PARTS = {".git", ".venv", "venv", "build", "dist", "__pycache__"}
CODE_SUFFIXES = {
    ".py",
    ".sh",
    ".js",
    ".css",
    ".html",
    ".yml",
    ".yaml",
    ".toml",
    ".vectis",
}
FORBIDDEN_PUBLIC_PATHS = (
    ".autonomy",
    "artifacts",
    "competition",
    "docs/submission",
    "tools/spectral_core_controller.py",
    "tools/vectis_task_contracts.py",
    "tools/task-gates",
)
GENERIC_PHRASES = (
    "in today's fast paced world",
    "game changing",
    "revolutionary solution",
    "seamlessly integrates",
)


def iter_files() -> list[Path]:
    """Return repository files that are part of the checked product surface."""
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def markdown_prose_violations(path: Path, text: str) -> list[str]:
    """Check branding and Ghost Five prose rules outside fenced code blocks."""
    problems: list[str] = []
    relative = path.relative_to(ROOT)

    if BRAND not in "\n".join(text.splitlines()[:12]):
        problems.append(f"{relative}: missing Ghost Five brand header")

    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if "—" in line or "–" in line:
            problems.append(
                f"{relative}:{number}: dash punctuation is not allowed in prose"
            )

        if re.match(r"^\s*-\s+", line):
            problems.append(
                f"{relative}:{number}: replace dash bullets with paragraphs, "
                "numbered lists, tables, or star bullets"
            )

        lowered = line.lower()
        for phrase in GENERIC_PHRASES:
            if phrase in lowered:
                problems.append(
                    f"{relative}:{number}: remove generic phrase {phrase!r}"
                )

    return problems


def code_header_violations(path: Path, text: str) -> list[str]:
    """Require a Ghost Five purpose header on code and configuration files."""
    if path.suffix.lower() not in CODE_SUFFIXES:
        return []

    head = "\n".join(text.splitlines()[:8])
    if BRAND not in head:
        return [
            f"{path.relative_to(ROOT)}: missing Ghost Five code header"
        ]

    return []


def main() -> int:
    """Run repository policy checks and return a shell friendly exit code."""
    problems: list[str] = []

    for relative in FORBIDDEN_PUBLIC_PATHS:
        if (ROOT / relative).exists():
            problems.append(
                f"{relative}: internal path is not allowed in the public product tree"
            )

    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if path.suffix.lower() == ".md":
            problems.extend(markdown_prose_violations(path, text))

        problems.extend(code_header_violations(path, text))

    if problems:
        print("SPECTRAL CORE REPOSITORY POLICY FAILED")
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1

    print("Spectral Core repository policy: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
