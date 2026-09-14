from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]

BACKLOG_PATH = ROOT / "competition" / "backlog.json"
ROLES_PATH = ROOT / "competition" / "roles.json"
MANIFEST_PATH = ROOT / "competition" / "manifest.md"
POLICY_PATH = ROOT / "competition" / "autonomy-policy.md"

RUNTIME = ROOT / ".autonomy" / "runtime"
STATE_PATH = RUNTIME / "state.json"
LOG_PATH = RUNTIME / "controller.log"
STOP_PATH = ROOT / ".autonomy" / "STOP"

OLLAMA_URL = os.environ.get(
    "VECTIS_OLLAMA_URL",
    "http://100.88.223.49:11434",
).rstrip("/")

REQUESTED_MODEL = os.environ.get(
    "VECTIS_MODEL",
    "",
).strip()

LOOP_DELAY = int(
    os.environ.get(
        "VECTIS_LOOP_DELAY",
        "20",
    )
)

MAX_FILES = 12
MAX_FILE_SIZE = 150_000
MAX_REPAIR_FAILURES = 6
MAX_STRUCTURED_RESPONSE_ATTEMPTS = 3

PROTECTED = {
    "competition/manifest.md",
    "competition/provenance.md",
    "competition/autonomy-policy.md",
    "competition/backlog.json",
    "competition/roles.json",
    "tools/spectral_core_controller.py",
    "tools/quality-gate.sh",
    ".gitignore",
}

ALLOWED_PREFIXES = (
    "src/",
    "tests/",
    "docs/",
    "examples/",
    "tools/",
    "artifacts/qa/",
)


TASK_FILE_RULES = {
    "COMP-001": {
        "src/vectis/source_position.py",
        "src/vectis/source_span.py",
        "src/vectis/token.py",
        "tests/test_source_position.py",
        "tests/test_source_span.py",
        "tests/test_token.py",
    },
    "COMP-002": {
        "src/vectis/lexer.py",
        "tests/test_lexer.py",
    },
}


def task_file_boundary(
    task_id: str,
) -> str:
    """Describe an exact per-task write boundary when one exists."""
    allowed = TASK_FILE_RULES.get(task_id)

    if not allowed:
        return (
            "No additional task-specific file restriction. "
            "Normal repository write boundaries apply."
        )

    return "\n".join(
        "- " + item
        for item in sorted(allowed)
    )


def validate_task_file_boundary(
    task_id: str,
    proposal: dict[str, Any],
) -> None:
    """Reject proposals that write outside an exact task boundary."""
    allowed = TASK_FILE_RULES.get(task_id)

    if not allowed:
        return

    proposed = {
        str(file["path"])
        for file in proposal["files"]
    }

    outside = sorted(
        proposed - allowed
    )

    if outside:
        raise ValueError(
            "Task "
            + task_id
            + " proposal attempted files outside its "
            + "deterministic boundary: "
            + ", ".join(outside)
            + ". Allowed files: "
            + ", ".join(sorted(allowed))
        )


def now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def log(message: str) -> None:
    RUNTIME.mkdir(
        parents=True,
        exist_ok=True,
    )

    line = f"[{now()}] {message}"

    print(
        line,
        flush=True,
    )

    with LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            line + "\n"
        )


def run(
    args: list[str],
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


def read_json(
    path: pathlib.Path,
) -> Any:
    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def write_json(
    path: pathlib.Path,
    value: Any,
) -> None:
    temp = path.with_suffix(
        path.suffix + ".tmp"
    )

    temp.write_text(
        json.dumps(
            value,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    temp.replace(path)


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "iterations": 0,
            "current_task": None,
            "repair_failures": 0,
            "last_feedback": "",
            "last_quality_output": "",
            "started_at": now(),
        }

    return read_json(
        STATE_PATH
    )


def save_state(
    state: dict[str, Any],
) -> None:
    RUNTIME.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_json(
        STATE_PATH,
        state,
    )


def ollama_models() -> list[str]:
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/tags"
    )

    with urllib.request.urlopen(
        request,
        timeout=10,
    ) as response:
        payload = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

    names = []

    for item in payload.get(
        "models",
        [],
    ):
        name = item.get("name")

        if isinstance(
            name,
            str,
        ):
            names.append(name)

    return names


def choose_model() -> str:
    models = ollama_models()

    if not models:
        raise RuntimeError(
            "No Ollama models installed."
        )

    if REQUESTED_MODEL:
        if REQUESTED_MODEL not in models:
            raise RuntimeError(
                "Requested model unavailable: "
                + REQUESTED_MODEL
            )

        return REQUESTED_MODEL

    preferences = (
        "qwen3-coder",
        "qwen2.5-coder",
        "qwen3",
        "deepseek-coder",
        "codestral",
        "codellama",
    )

    for preference in preferences:
        for model in models:
            if preference in model.lower():
                return model

    return models[0]


def generate(
    model: str,
    prompt: str,
) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": 0.10,
            "num_ctx": 16384,
            "num_predict": 4096,
        },
    }

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=420,
    ) as response:
        result = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

    text = result.get(
        "response"
    )

    if not isinstance(
        text,
        str,
    ) or not text.strip():
        raise RuntimeError(
            "Model returned empty response."
        )

    return text.strip()


def generate_parsed(
    model: str,
    prompt: str,
    parser: Any,
    label: str,
) -> Any:
    """Generate and validate structured output with bounded retries."""

    last_error: Exception | None = None
    correction = ""

    for attempt in range(
        1,
        MAX_STRUCTURED_RESPONSE_ATTEMPTS + 1,
    ):
        attempt_prompt = prompt

        if correction:
            attempt_prompt += (
                "\n\nSTRUCTURED OUTPUT CORRECTION:\n"
                + correction
                + "\n"
                + "Return a complete JSON object only. "
                + "Do not use Markdown fences. "
                + "Do not add commentary before or after JSON."
            )

        raw = generate(
            model,
            attempt_prompt,
        )

        try:
            return parser(raw)

        except Exception as exc:
            last_error = exc

            log(
                f"{label} structured response rejected "
                f"attempt {attempt}/"
                f"{MAX_STRUCTURED_RESPONSE_ATTEMPTS}: "
                f"{type(exc).__name__}: {exc}"
            )

            correction = (
                f"Your previous response was rejected: "
                f"{type(exc).__name__}: {exc}. "
                f"Correct that exact problem. "
                f"Do not propose files under competition/. "
                f"Writable prefixes are only src/, tests/, docs/, "
                f"examples/, tools/, and artifacts/qa/."
            )

    raise RuntimeError(
        f"{label} failed structured validation after "
        f"{MAX_STRUCTURED_RESPONSE_ATTEMPTS} attempts: "
        f"{last_error}"
    )


def next_task(
    backlog: dict[str, Any],
) -> dict[str, Any] | None:
    for task in backlog["tasks"]:
        if task["status"] != "done":
            return task

    return None


def validate_path(
    raw: str,
) -> pathlib.Path:
    path = pathlib.Path(raw)

    if path.is_absolute():
        raise ValueError(
            "Absolute paths prohibited."
        )

    if ".." in path.parts:
        raise ValueError(
            "Path traversal prohibited."
        )

    normalized = path.as_posix()

    if normalized in PROTECTED:
        raise ValueError(
            f"Protected file: {normalized}"
        )

    if not any(
        normalized.startswith(prefix)
        for prefix in ALLOWED_PREFIXES
    ):
        raise ValueError(
            f"Path outside allowed area: {normalized}"
        )

    return path


def repository_context(
    limit: int = 32_000,
) -> str:
    sections: list[str] = []
    used = 0

    candidates: list[pathlib.Path] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(
            ROOT
        ).as_posix()

        if relative.startswith(
            ".git/"
        ):
            continue

        if relative.startswith(
            ".autonomy/"
        ):
            continue

        if relative.startswith(
            "artifacts/runtime/"
        ):
            continue

        if relative in {
            "competition/backlog.json",
            "competition/roles.json",
            "tools/spectral_core_controller.py",
        }:
            continue

        if path.stat().st_size > 40_000:
            continue

        candidates.append(path)

    for path in sorted(candidates):
        relative = path.relative_to(
            ROOT
        ).as_posix()

        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        section = (
            "\n===== "
            + relative
            + " =====\n"
            + content
            + "\n"
        )

        if used + len(section) > limit:
            continue

        sections.append(section)
        used += len(section)

    return "".join(sections)


def completed_task_baseline(
    current_task_id: str,
) -> str:
    """Describe completed work that later tasks must preserve."""
    data = json.loads(
        BACKLOG_PATH.read_text(encoding="utf-8")
    )
    tasks = (
        data
        if isinstance(data, list)
        else data.get("tasks", [])
    )

    completed = []

    for task in tasks:
        task_id = str(task.get("id", ""))

        if task_id == current_task_id:
            continue

        if task.get("status") != "done":
            continue

        completed.append(
            "- "
            + task_id
            + ": "
            + str(task.get("title", ""))
            + " // implementation commit: "
            + str(
                task.get(
                    "implementation_commit",
                    "unknown",
                )
            )
        )

    if not completed:
        return "(none)"

    return "\n".join(completed)


def specialist_prompt(
    task: dict[str, Any],
    role: dict[str, Any],
    state: dict[str, Any],
) -> str:
    acceptance = "\n".join(
        "- " + item
        for item in task["acceptance"]
    )

    return f"""
You are the Spectral Core specialist role: {role["name"]}.

ROLE MISSION:
{role["mission"]}

You are contributing to VECTIS, a real deterministic DSL being built for
Syntax Summit.

ACTIVE TASK:
{task["id"]}: {task["title"]}

ACCEPTANCE:
{acceptance}

PREVIOUS FAILURE OR REVIEW FEEDBACK:
{state.get("last_feedback") or "(none)"}

PREVIOUS QUALITY OUTPUT:
{state.get("last_quality_output") or "(none)"}

COMPLETED BASELINE TASKS:
{completed_task_baseline(task["id"])}

TASK-SPECIFIC FILE BOUNDARY:
{task_file_boundary(task["id"])}

If an exact task-specific boundary is listed above, you MUST
return only files from that list. Do not implement future tasks,
even when you can anticipate their requirements.

BASELINE DISCIPLINE:
Completed tasks are established dependencies of the current
task. Read and reuse their APIs and behavior. Do not recreate,
replace, redesign, or weaken completed-task artifacts merely to
make the current task easier. Modify an established artifact
only when the CURRENT task acceptance criteria materially
require that modification. If such a modification is necessary,
keep it minimal and preserve all previously tested behavior.

Your tests must exercise the CURRENT task. Do not replace tests
for completed tasks with alternate assumptions about their APIs.

PROJECT CONTEXT:
{repository_context()}

Return JSON only:

{{
  "summary": "what you changed and why",
  "ready_for_review": true,
  "commit_message": "type: concise message",
  "files": [
    {{
      "path": "relative/path",
      "content": "complete replacement contents"
    }}
  ]
}}

Rules:

- Work only on this task.
- Return complete file contents, not diffs.
- Maximum {MAX_FILES} files.
- Do not alter protected competition or controller files.
- NEVER create or modify anything under competition/.
- The ONLY writable prefixes are:
  src/
  tests/
  docs/
  examples/
  tools/
  artifacts/qa/
- Do not create symbolic links.
- Do not execute commands.
- Do not modify files outside those exact writable prefixes.
- Do not weaken valid existing tests.
- Add tests whenever behavior changes.
- Keep documentation consistent with behavior.
- Prefer correctness and coherent design over feature quantity.
""".strip()


def parse_change(
    text: str,
) -> dict[str, Any]:
    value = json.loads(text)

    expected = {
        "summary",
        "ready_for_review",
        "commit_message",
        "files",
    }

    if set(value) != expected:
        raise ValueError(
            "Invalid proposal JSON keys."
        )

    if not isinstance(
        value["files"],
        list,
    ):
        raise ValueError(
            "files must be list"
        )

    if len(
        value["files"]
    ) > MAX_FILES:
        raise ValueError(
            "Too many files."
        )

    seen = set()

    for file in value["files"]:
        if set(file) != {
            "path",
            "content",
        }:
            raise ValueError(
                "Invalid file object."
            )

        path = validate_path(
            file["path"]
        )

        if path in seen:
            raise ValueError(
                "Duplicate path."
            )

        seen.add(path)

        content = file["content"]

        if not isinstance(
            content,
            str,
        ):
            raise ValueError(
                "File content must be string."
            )

        if len(
            content.encode("utf-8")
        ) > MAX_FILE_SIZE:
            raise ValueError(
                "Generated file too large."
            )

    return value


def apply_change(
    proposal: dict[str, Any],
) -> None:
    for file in proposal["files"]:
        relative = validate_path(
            file["path"]
        )

        target = ROOT / relative

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            file["content"],
            encoding="utf-8",
        )


def quality_gate() -> tuple[bool, str]:
    result = run(
        [
            "bash",
            "tools/quality-gate.sh",
        ]
    )

    return (
        result.returncode == 0,
        result.stdout,
    )


def diff_text() -> str:
    return run(
        [
            "git",
            "diff",
            "--",
            ".",
        ]
    ).stdout[-100_000:]


def reviewer_prompt(
    task: dict[str, Any],
    reviewer: dict[str, Any],
    quality_output: str,
) -> str:
    acceptance = "\n".join(
        "- " + item
        for item in task["acceptance"]
    )

    return f"""
You are Spectral Core reviewer: {reviewer["name"]}.

REVIEW MISSION:
{reviewer["mission"]}

Review the implementation for this task only.

TASK:
{task["id"]}: {task["title"]}

ACCEPTANCE:
{acceptance}

COMPLETED BASELINE TASKS:
{completed_task_baseline(task["id"])}

BASELINE REVIEW RULE:
Reject implementations that unnecessarily recreate, replace,
redesign, or weaken artifacts belonging to completed tasks.
Changes to established artifacts are acceptable only when the
CURRENT task acceptance criteria materially require them and
previously tested behavior remains intact. Tests for the current
task must not invent alternate APIs for completed components.

QUALITY GATE:
{quality_output[-20000:]}

CURRENT PROJECT STATE:
{repository_context(limit=48_000)}

CURRENT TRACKED DIFF:
{diff_text()}

The CURRENT PROJECT STATE is authoritative for newly created
files that may not appear in the tracked Git diff.

Return JSON only:

{{
  "approved": true,
  "summary": "review conclusion",
  "issues": []
}}

Approve only if:

- every acceptance criterion is materially satisfied
- implementation is coherent with existing architecture
- tests meaningfully cover changed behavior
- documentation is accurate
- no obvious safety boundary is weakened
- no unrelated feature expansion is introduced

If not approved, explain concrete repair actions in issues.
""".strip()


def parse_review(
    text: str,
) -> dict[str, Any]:
    value = json.loads(text)

    if set(value) != {
        "approved",
        "summary",
        "issues",
    }:
        raise ValueError(
            "Invalid review JSON."
        )

    if not isinstance(
        value["approved"],
        bool,
    ):
        raise ValueError(
            "approved must be boolean."
        )

    if not isinstance(
        value["issues"],
        list,
    ):
        raise ValueError(
            "issues must be list."
        )

    return value


def reset_to_head() -> None:
    run(
        [
            "git",
            "reset",
            "--hard",
            "HEAD",
        ]
    )

    run(
        [
            "git",
            "clean",
            "-fd",
        ]
    )


def commit_change(
    message: str,
) -> str:
    run(
        [
            "git",
            "add",
            "-A",
        ]
    )

    check = run(
        [
            "git",
            "diff",
            "--cached",
            "--check",
        ]
    )

    if check.returncode != 0:
        raise RuntimeError(
            check.stdout
        )

    files = run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
        ]
    ).stdout.strip()

    if not files:
        raise RuntimeError(
            "No staged change."
        )

    safe = message.strip()

    if not safe:
        safe = (
            "feat: advance VECTIS implementation"
        )

    run(
        [
            "git",
            "commit",
            "-m",
            safe[:100],
        ]
    )

    return run(
        [
            "git",
            "rev-parse",
            "--short",
            "HEAD",
        ]
    ).stdout.strip()


def finish_task(
    backlog: dict[str, Any],
    task: dict[str, Any],
    commit: str,
) -> None:
    for current in backlog["tasks"]:
        if current["id"] == task["id"]:
            current["status"] = "done"
            current["completed_at"] = now()
            current["implementation_commit"] = commit

    write_json(
        BACKLOG_PATH,
        backlog,
    )

    run(
        [
            "git",
            "add",
            "competition/backlog.json",
        ]
    )

    run(
        [
            "git",
            "commit",
            "-m",
            f"chore: complete {task['id']}",
        ]
    )


def completion_report(
    backlog: dict[str, Any],
) -> None:
    target = (
        ROOT
        / "artifacts"
        / "qa"
        / "autonomous-development-complete.md"
    )

    lines = [
        "# VECTIS Autonomous Development Completion",
        "",
        f"Completed: {now()}",
        "",
        "## Backlog",
        "",
    ]

    for task in backlog["tasks"]:
        lines.append(
            f"- {task['id']}: "
            f"{task['title']} — "
            f"{task['status']}"
        )

    target.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    RUNTIME.mkdir(
        parents=True,
        exist_ok=True,
    )

    log(
        "Spectral Core multi-role controller starting."
    )

    model = choose_model()

    log(
        f"Model selected: {model}"
    )

    roles = read_json(
        ROLES_PATH
    )["roles"]

    while True:
        if STOP_PATH.exists():
            log(
                "STOP file detected. Controller exiting cleanly."
            )
            return 0

        backlog = read_json(
            BACKLOG_PATH
        )

        task = next_task(
            backlog
        )

        if task is None:
            log(
                "Backlog complete. Running final quality gate."
            )

            passed, output = quality_gate()

            if not passed:
                log(
                    "Final quality gate failed unexpectedly."
                )

                state = load_state()
                state[
                    "last_quality_output"
                ] = output[-30000:]

                save_state(state)

                time.sleep(
                    LOOP_DELAY
                )

                continue

            completion_report(
                backlog
            )

            run(
                [
                    "git",
                    "add",
                    "-A",
                ]
            )

            run(
                [
                    "git",
                    "commit",
                    "-m",
                    "docs: record VECTIS autonomous completion",
                ]
            )

            log(
                "All approved work complete. Controller stopping."
            )

            return 0

        state = load_state()

        state["iterations"] = (
            int(
                state.get(
                    "iterations",
                    0,
                )
            )
            + 1
        )

        state["current_task"] = task[
            "id"
        ]

        save_state(
            state
        )

        role = roles[
            task["role"]
        ]

        reviewer = roles[
            task["reviewer"]
        ]

        log(
            f"Iteration {state['iterations']} // "
            f"{task['id']} // "
            f"{role['name']} -> "
            f"{reviewer['name']}"
        )

        try:
            proposal = generate_parsed(
                model,
                specialist_prompt(
                    task,
                    role,
                    state,
                ),
                parse_change,
                f"{task['id']} specialist",
            )

            if not proposal["files"]:
                raise RuntimeError(
                    "Specialist returned no files."
                )

            validate_task_file_boundary(
                task["id"],
                proposal,
            )

            apply_change(
                proposal
            )

            passed, quality_output = (
                quality_gate()
            )

            state[
                "last_quality_output"
            ] = quality_output[-30000:]

            if not passed:
                state["repair_failures"] = (
                    int(
                        state.get(
                            "repair_failures",
                            0,
                        )
                    )
                    + 1
                )

                state[
                    "last_feedback"
                ] = (
                    "Quality gate failed. "
                    "Repair the implementation based on the "
                    "quality output."
                )

                save_state(
                    state
                )

                log(
                    f"{task['id']} quality failure "
                    f"{state['repair_failures']}/"
                    f"{MAX_REPAIR_FAILURES}"
                )

                if (
                    state["repair_failures"]
                    >= MAX_REPAIR_FAILURES
                ):
                    reset_to_head()

                    state[
                        "repair_failures"
                    ] = 0

                    diagnostic = (
                        state.get(
                            "last_quality_output",
                            "",
                        )
                        or state.get(
                            "last_feedback",
                            "",
                        )
                    )

                    if len(diagnostic) > 12_000:
                        diagnostic = diagnostic[-12_000:]

                    state[
                        "last_feedback"
                    ] = (
                        "The previous candidate was rolled back "
                        "to the last green commit after repeated "
                        "failures. Preserve behavior that passed. "
                        "Repair the smallest root cause supported "
                        "by the deterministic evidence below. "
                        "Do not redesign unrelated parts of the "
                        "task.\n\n"
                        "LAST FAILURE EVIDENCE:\n"
                        + diagnostic
                    )

                    save_state(
                        state
                    )

                    log(
                        "Repeated failure threshold reached; "
                        "returned to last green commit."
                    )

                time.sleep(
                    LOOP_DELAY
                )

                continue

            review = generate_parsed(
                model,
                reviewer_prompt(
                    task,
                    reviewer,
                    quality_output,
                ),
                parse_review,
                f"{task['id']} reviewer",
            )

            if not review["approved"]:
                state["repair_failures"] = (
                    int(
                        state.get(
                            "repair_failures",
                            0,
                        )
                    )
                    + 1
                )

                state[
                    "last_feedback"
                ] = (
                    review["summary"]
                    + "\n"
                    + "\n".join(
                        "- " + str(issue)
                        for issue in review[
                            "issues"
                        ]
                    )
                )

                save_state(
                    state
                )

                log(
                    f"{task['id']} rejected by "
                    f"{reviewer['name']}."
                )

                if (
                    state["repair_failures"]
                    >= MAX_REPAIR_FAILURES
                ):
                    reset_to_head()

                    state[
                        "repair_failures"
                    ] = 0

                    state[
                        "last_feedback"
                    ] = (
                        "Reviewer rejected the prior design "
                        "repeatedly. Start again from the last "
                        "green commit with a different approach."
                    )

                    save_state(
                        state
                    )

                time.sleep(
                    LOOP_DELAY
                )

                continue

            commit = commit_change(
                proposal[
                    "commit_message"
                ]
            )

            log(
                f"{task['id']} implementation approved "
                f"and committed at {commit}."
            )

            finish_task(
                backlog,
                task,
                commit,
            )

            state[
                "repair_failures"
            ] = 0

            state[
                "last_feedback"
            ] = ""

            state[
                "last_quality_output"
            ] = ""

            save_state(
                state
            )

            log(
                f"{task['id']} complete."
            )

        except Exception as exc:
            state = load_state()

            state["repair_failures"] = (
                int(
                    state.get(
                        "repair_failures",
                        0,
                    )
                )
                + 1
            )

            state[
                "last_feedback"
            ] = (
                f"Controller exception: "
                f"{type(exc).__name__}: {exc}"
            )

            log(
                state[
                    "last_feedback"
                ]
            )

            log(
                f"{task['id']} controller failure "
                f"{state['repair_failures']}/"
                f"{MAX_REPAIR_FAILURES}"
            )

            if (
                state["repair_failures"]
                >= MAX_REPAIR_FAILURES
            ):
                reset_to_head()

                state[
                    "repair_failures"
                ] = 0

                state[
                    "last_feedback"
                ] = (
                    "Repeated controller or model-output failures "
                    "caused rollback to the last green commit. "
                    "Use a smaller, simpler implementation and "
                    "strictly obey the permitted output paths."
                )

                log(
                    f"{task['id']} failure threshold reached; "
                    "reset to last green commit."
                )

            save_state(
                state
            )

        time.sleep(
            LOOP_DELAY
        )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
