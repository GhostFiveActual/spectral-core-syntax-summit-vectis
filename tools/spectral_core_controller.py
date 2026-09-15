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
MAX_STRUCTURED_RESPONSE_ATTEMPTS = 5

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


from vectis_task_contracts import TASK_FILE_RULES, TASK_SPECS


def task_file_boundary(
    task_id: str,
) -> str:
    """Describe an exact per-task write boundary when one exists."""
    allowed = TASK_FILE_RULES.get(task_id)

    if not allowed:
        return (
            "BLOCKED: no deterministic task-specific "
            "file boundary is registered."
        )

    boundary = "\n".join(
        "- " + item
        for item in sorted(allowed)
    )

    return (
        boundary
        + "\n\nITERATION OUTPUT POLICY:\n"
        + "- Change no more than 2 files in one proposal.\n"
        + "- Keep total proposed file content at or below 12000 characters.\n"
        + "- Work incrementally and omit unchanged files.\n"
        + "- Never change completed-task artifacts unless explicitly allowed."
    )


def validate_task_file_boundary(
    task_id: str,
    proposal: dict[str, Any],
) -> None:
    """Reject proposals that write outside an exact task boundary."""
    allowed = TASK_FILE_RULES.get(task_id)

    if not allowed:
        raise ValueError(
            "Task "
            + task_id
            + " has no deterministic file boundary. "
            + "Refusing broad repository writes."
        )

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

    if len(proposed) > 2:
        raise ValueError(
            "Task "
            + task_id
            + " proposal exceeded unattended file-count budget: "
            + str(len(proposed))
            + " files; maximum is 2."
        )

    total_content = sum(
        len(str(file.get("content", "")))
        for file in proposal["files"]
    )

    if total_content > 12000:
        raise ValueError(
            "Task "
            + task_id
            + " proposal exceeded unattended structured-output budget: "
            + str(total_content)
            + " characters; maximum is 12000. "
            + "Split work across iterations."
        )



VECTIS_CHANGE_HEADER = "VECTIS_CHANGE_V1"
VECTIS_CONTENT_BEGIN = "<<<VECTIS_CONTENT_7F4A2B>>>"
VECTIS_CONTENT_END = "<<<VECTIS_END_7F4A2B>>>"


def failure_target_from_evidence(
    task_id: str,
    evidence: str,
) -> str | None:
    import re

    allowed = TASK_FILE_RULES.get(
        task_id,
        set(),
    )
    spec = TASK_SPECS.get(
        task_id,
        {},
    )

    def normalize_candidate(
        raw: str,
    ) -> str | None:
        raw = raw.strip().rstrip(
            ",:)"
        )

        try:
            candidate_path = pathlib.Path(
                raw
            )

            if candidate_path.is_absolute():
                candidate = (
                    candidate_path
                    .resolve()
                    .relative_to(
                        ROOT.resolve()
                    )
                    .as_posix()
                )
            else:
                candidate = (
                    candidate_path
                    .as_posix()
                )
        except (OSError, ValueError):
            return None

        if candidate in allowed:
            return candidate

        return None

    # Explicit deterministic artifact errors identify the owner directly.
    for pattern in (
        r"Error compiling [\"']([^\"']+)[\"']",
        r"([^\s:]+\.py)\s+has\s+\d+\s+tests;",
        r"([^\s:]+\.md)\s+missing required concept",
    ):
        for match in re.finditer(
            pattern,
            evidence,
            flags=re.IGNORECASE,
        ):
            candidate = normalize_candidate(
                match.group(1)
            )

            if candidate is not None:
                return candidate

    # Python traceback frames are ordered caller -> callee. The deepest
    # task-owned frame is therefore the strongest runtime ownership signal.
    traceback_candidates = []

    for match in re.finditer(
        r"File [\"']([^\"']+\.py)[\"']",
        evidence,
        flags=re.IGNORECASE,
    ):
        candidate = normalize_candidate(
            match.group(1)
        )

        if candidate is not None:
            traceback_candidates.append(
                candidate
            )

    if traceback_candidates:
        return traceback_candidates[-1]

    lower = evidence.lower()

    # Public API failures without a useful project traceback still map to
    # the task module that owns the contracted symbol.
    for module_name, symbols in spec.get(
        "python_symbols",
        {},
    ).items():
        module_path = (
            "src/"
            + module_name.replace(
                ".",
                "/",
            )
            + ".py"
        )

        if module_path not in allowed:
            continue

        markers = (
            f"- {module_name}:",
            f"import: {module_name} FAIL",
            f"{module_name} missing symbol",
        )

        if any(
            marker in evidence
            for marker in markers
        ):
            return module_path

        module_named_in_exception = bool(
            re.search(
                r"(?:ImportError|AttributeError|ModuleNotFoundError):[^\n]*"
                + re.escape(
                    module_name
                ),
                evidence,
                flags=re.IGNORECASE,
            )
        )

        for symbol in symbols:
            if (
                str(symbol) in evidence
                and (
                    module_named_in_exception
                    or "missing symbol" in lower
                )
            ):
                return module_path

    # unittest collection failures can identify the task test file even when
    # a path frame is absent from compact evidence.
    test_file = spec.get(
        "test_file"
    )

    if (
        isinstance(
            test_file,
            str,
        )
        and test_file in allowed
    ):
        test_module = pathlib.Path(
            test_file
        ).stem
        test_name = pathlib.Path(
            test_file
        ).name

        test_patterns = (
            r"(?:ERROR|FAIL):[^\n]*\b"
            + re.escape(
                test_module
            )
            + r"\b",
            r"_FailedTest\."
            + re.escape(
                test_module
            )
            + r"\b",
            r"Failed to import test module:\s*"
            + re.escape(
                test_module
            )
            + r"\b",
            r"ERROR collecting[^\n]*"
            + re.escape(
                test_name
            ),
        )

        if any(
            re.search(
                pattern,
                evidence,
                flags=re.IGNORECASE,
            )
            for pattern in test_patterns
        ):
            return test_file

    # Missing artifacts are staged progression after active failures clear.
    for match in re.finditer(
        r"missing required artifact:\s*([^\s]+)",
        evidence,
        flags=re.IGNORECASE,
    ):
        candidate = normalize_candidate(
            match.group(1)
        )

        if candidate is not None:
            return candidate

    return None

def next_task_target(
    task_id: str,
    state: dict[str, Any],
) -> str:
    # Prefer manifest dependency order when an earlier required artifact
    # is missing. Otherwise use explicit deterministic failure evidence.
    allowed = TASK_FILE_RULES.get(task_id)

    if not allowed:
        raise RuntimeError(
            "Task "
            + task_id
            + " has no deterministic file boundary."
        )

    spec = TASK_SPECS.get(task_id, {})
    required = [
        relative
        for relative in spec.get(
            "required_files",
            [],
        )
        if relative in allowed
    ]

    evidence = (
        str(state.get("last_quality_output", ""))
        + "\n"
        + str(state.get("last_feedback", ""))
    )

    failure_target = failure_target_from_evidence(
        task_id,
        evidence,
    )

    missing = []

    for relative in required:
        target = ROOT / relative

        if (
            not target.is_file()
            or target.stat().st_size == 0
        ):
            missing.append(relative)

    if missing:
        first_missing = missing[0]

        if failure_target is None:
            return first_missing

        if failure_target not in required:
            return first_missing

        if (
            required.index(first_missing)
            <= required.index(failure_target)
        ):
            return first_missing

    if failure_target is not None:
        return failure_target

    if missing:
        return missing[0]

    test_file = spec.get("test_file")

    if (
        isinstance(test_file, str)
        and test_file in allowed
    ):
        return test_file

    return sorted(allowed)[0]

def specialist_transport_prompt(
    task: dict[str, Any],
    role: dict[str, Any],
    state: dict[str, Any],
    target: str | None = None,
) -> str:
    # The controller owns the path. For an existing broken artifact, use a
    # deliberately compact repair prompt instead of the full repository
    # briefing so the model focuses on the exact failing file and evidence.
    if target is None:
        target = next_task_target(
            task["id"],
            state,
        )

    target_path = validate_path(
        target
    )

    acceptance = "\n".join(
        "- " + str(item)
        for item in task.get(
            "acceptance",
            [],
        )
    )

    feedback = str(
        state.get(
            "last_feedback",
            "",
        )
        or "(none)"
    )

    quality = str(
        state.get(
            "last_quality_output",
            "",
        )
        or "(none)"
    )

    if len(feedback) > 4_000:
        feedback = feedback[-4_000:]

    if len(quality) > 8_000:
        quality = quality[-8_000:]

    authority = authoritative_dependency_context(
        task["id"],
        target,
    )

    if len(authority) > 12_000:
        authority = authority[-12_000:]

    if target_path.exists():
        current_body = target_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if len(current_body) > 12_000:
            current_body = current_body[-12_000:]

        return (
            "You are repairing one existing VECTIS task artifact.\n\n"
            + "ROLE:\n"
            + str(role.get("name", "specialist"))
            + "\n\n"
            + "ACTIVE TASK:\n"
            + str(task["id"])
            + ": "
            + str(task["title"])
            + "\n\n"
            + "ACCEPTANCE:\n"
            + acceptance
            + "\n\n"
            + "TARGET FILE:\n"
            + target
            + "\n\n"
            + "DETERMINISTIC FAILURE / REVIEW FEEDBACK:\n"
            + feedback
            + "\n\n"
            + "DETERMINISTIC QUALITY EVIDENCE:\n"
            + quality
            + "\n\n"
            + "AUTHORITATIVE DEPENDENCY CONTEXT:\n"
            + authority
            + "\n\n"
            + "CURRENT TARGET FILE CONTENTS:\n"
            + "<<<CURRENT_TARGET_BODY>>>\n"
            + current_body
            + "\n<<<END_CURRENT_TARGET_BODY>>>\n\n"
            + "REPAIR DIRECTIVE:\n"
            + "Repair the smallest root cause demonstrated by the "
              "deterministic evidence. The checked-in/current source APIs "
              "and authoritative dependency context outrank assumptions. "
              "Do not preserve an import, symbol, constructor, or call shape "
              "that the evidence proves is invalid. Do not rewrite unrelated "
              "completed-task behavior. Your returned file MUST differ from "
              "the current target body when a failure is present.\n\n"
            + "OUTPUT CONTRACT:\n"
            + "Return ONLY the complete replacement contents of the TARGET "
              "FILE. Do not return JSON, a path, a commit message, commentary, "
              "or multiple files. A single outer Markdown code fence is "
              "tolerated by the controller for source files, but plain file "
              "contents are preferred."
        )

    # New artifact: no repair body exists, so retain task acceptance and
    # authoritative dependencies but still avoid the large generic repo dump.
    return (
        "You are creating one missing VECTIS task artifact.\n\n"
        + "ROLE:\n"
        + str(role.get("name", "specialist"))
        + "\n\n"
        + "ACTIVE TASK:\n"
        + str(task["id"])
        + ": "
        + str(task["title"])
        + "\n\n"
        + "ACCEPTANCE:\n"
        + acceptance
        + "\n\n"
        + "TARGET FILE:\n"
        + target
        + "\n\n"
        + "LATEST TASK EVIDENCE:\n"
        + quality
        + "\n\n"
        + "AUTHORITATIVE DEPENDENCY CONTEXT:\n"
        + authority
        + "\n\n"
        + "Create exactly this required artifact using the established "
          "VECTIS APIs. Do not implement future tasks or invent project "
          "symbols that are absent from authoritative dependencies.\n\n"
        + "OUTPUT CONTRACT:\n"
        + "Return ONLY the complete contents of the TARGET FILE. Do not "
          "return JSON, a path, a commit message, commentary, or another "
          "artifact."
    )

def parse_specialist_transport(
    text: str,
    target: str,
) -> dict[str, Any]:
    # Convert one model response directly into the controller-owned file.
    if not isinstance(
        text,
        str,
    ):
        raise ValueError(
            "Specialist body must be text."
        )

    path_value = validate_path(
        target
    ).as_posix()

    content = text.strip(
        "\r\n"
    )

    if not content.strip():
        raise ValueError(
            "Specialist body is empty."
        )

    suffix = pathlib.Path(
        path_value
    ).suffix.lower()

    code_suffixes = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".sh",
        ".vectis",
    }

    if (
        suffix in code_suffixes
        and "```" in content
    ):
        stripped = content.strip()
        lines = stripped.splitlines()

        if len(lines) < 3:
            raise ValueError(
                "Source artifact contains incomplete Markdown fencing."
            )

        opening = lines[0].strip()
        closing = lines[-1].strip()

        if (
            not opening.startswith("```")
            or closing != "```"
        ):
            raise ValueError(
                "Source artifact contains Markdown fencing or commentary "
                "outside one clean outer wrapper."
            )

        language = opening[3:]

        if (
            language
            and not all(
                character.isalnum()
                or character in "_.+-"
                for character in language
            )
        ):
            raise ValueError(
                "Source artifact wrapper has an invalid language label."
            )

        body_lines = lines[1:-1]

        if any(
            "```" in line
            for line in body_lines
        ):
            raise ValueError(
                "Source artifact contains embedded or multiple "
                "Markdown fences."
            )

        body = "\n".join(
            body_lines
        ).strip(
            "\r\n"
        )

        if not body.strip():
            raise ValueError(
                "Source artifact wrapper contains an empty body."
            )

        content = body

    if suffix == ".py":
        try:
            compile(
                content,
                path_value,
                "exec",
            )
        except SyntaxError as exc:
            line = (
                str(exc.lineno)
                if exc.lineno is not None
                else "unknown"
            )

            raise ValueError(
                "Generated Python syntax is invalid at line "
                + line
                + ": "
                + str(exc.msg)
            ) from exc

    content = content.rstrip(
        "\r\n"
    ) + "\n"

    size = len(
        content.encode(
            "utf-8"
        )
    )

    if size > 12_000:
        raise ValueError(
            "Direct specialist body exceeded 12000 UTF-8 bytes."
        )

    current_path = ROOT / path_value

    if current_path.exists():
        current = current_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        current = current.rstrip(
            "\r\n"
        ) + "\n"

        if content == current:
            raise ValueError(
                "Generated body is byte-equivalent to the current target "
                "after newline normalization. The deterministic failure is "
                "still unresolved; return a real repair that changes the "
                "target file."
            )

    if path_value.startswith(
        "docs/"
    ):
        commit_type = "docs"
    elif path_value.startswith(
        "tests/"
    ):
        commit_type = "test"
    else:
        commit_type = "feat"

    return {
        "files": [
            {
                "path": path_value,
                "content": content,
            }
        ],
        "commit_message": (
            commit_type
            + ": update "
            + pathlib.Path(
                path_value
            ).name
        ),
    }

def validate_specialist_target(
    task_id: str,
    state: dict[str, Any],
    proposal: dict[str, Any],
) -> None:
    # Require the proposal to match the controller-selected artifact.
    expected = next_task_target(
        task_id,
        state,
    )

    files = proposal.get(
        "files",
        [],
    )

    if len(files) != 1:
        raise ValueError(
            "Raw specialist transport must contain exactly one file."
        )

    actual = str(
        files[0].get(
            "path",
            "",
        )
    )

    if actual != expected:
        raise ValueError(
            "Task "
            + task_id
            + " specialist returned "
            + actual
            + " but controller selected "
            + expected
            + "."
        )


def validate_task_contract(
    task_id: str,
) -> None:
    # Fail closed before model generation when a task contract is absent.
    allowed = TASK_FILE_RULES.get(task_id)

    if not allowed:
        raise RuntimeError(
            "Task "
            + task_id
            + " has no deterministic TASK_FILE_RULES contract."
        )

    gate = (
        ROOT
        / "tools"
        / "task-gates"
        / f"{task_id}.sh"
    )

    if not gate.is_file():
        raise RuntimeError(
            "Task "
            + task_id
            + " has no deterministic acceptance gate: "
            + str(gate.relative_to(ROOT))
        )

    if not os.access(gate, os.X_OK):
        raise RuntimeError(
            "Task "
            + task_id
            + " acceptance gate is not executable: "
            + str(gate.relative_to(ROOT))
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
    *,
    json_mode: bool = True,
) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.10,
            "num_ctx": 16384,
            "num_predict": 4096,
        },
    }

    if json_mode:
        payload["format"] = "json"

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
    *,
    json_mode: bool = True,
) -> Any:
    """Generate and validate model output with bounded retries."""

    last_error: Exception | None = None
    correction = ""

    for attempt in range(
        1,
        MAX_STRUCTURED_RESPONSE_ATTEMPTS + 1,
    ):
        attempt_prompt = prompt

        if correction:
            if json_mode:
                attempt_prompt += (
                    "\n\nSTRUCTURED OUTPUT CORRECTION:\n"
                    + correction
                    + "\n"
                    + "Return a complete JSON object only. "
                    + "Do not use Markdown fences. "
                    + "Do not add commentary before or after JSON."
                )
            else:
                attempt_prompt += (
                    "\n\nDIRECT FILE-BODY CORRECTION:\n"
                    + correction
                    + "\n"
                    + "Return ONLY the complete contents of the "
                      "already-selected target file. Your response itself "
                      "is the complete file body. Do not return JSON, a "
                      "path, a commit message, transport headers, begin/end "
                      "markers, wrapper fences, or commentary."
                )

        raw = generate(
            model,
            attempt_prompt,
            json_mode=json_mode,
        )

        try:
            return parser(raw)

        except Exception as exc:
            last_error = exc

            response_kind = (
                "JSON"
                if json_mode
                else "raw"
            )

            log(
                f"{label} {response_kind} response rejected "
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

    validation_kind = (
        "JSON"
        if json_mode
        else "raw transport"
    )

    raise RuntimeError(
        f"{label} failed {validation_kind} validation after "
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



SPECIALIST_FAILURE_CONTEXT_MAX = 5_000
SPECIALIST_REPOSITORY_CONTEXT_MAX = 6_000
SPECIALIST_AUTHORITY_CONTEXT_MAX = 20_000

TASK_AUTHORITY_FILES: dict[str, tuple[str, ...]] = {
    "COMP-006": (
        "src/vectis/ast.py",
        "src/vectis/diagnostic.py",
        "src/vectis/parser.py",
        "docs/spec/semantic-model.md",
        "docs/spec/grammar.md",
    ),
    "IR-001": (
        "src/vectis/ast.py",
        "src/vectis/semantic.py",
        "src/vectis/diagnostic.py",
        "docs/design/semantic-analysis.md",
    ),
    "IR-002": (
        "src/vectis/ast.py",
        "src/vectis/semantic.py",
        "src/vectis/ir.py",
        "src/vectis/diagnostic.py",
    ),
    "RUN-001": (
        "src/vectis/compiler.py",
        "src/vectis/ir.py",
        "src/vectis/semantic.py",
        "src/vectis/diagnostic.py",
    ),
    "RUN-002": (
        "src/vectis/compiler.py",
        "src/vectis/ir.py",
        "src/vectis/semantic.py",
        "src/vectis/capabilities.py",
    ),
    "RUN-003": (
        "src/vectis/runtime.py",
        "src/vectis/capabilities.py",
        "src/vectis/compiler.py",
    ),
    "RUN-004": (
        "src/vectis/runtime.py",
        "src/vectis/capabilities.py",
        "src/vectis/adapters/filesystem.py",
    ),
    "RUN-005": (
        "src/vectis/runtime.py",
        "src/vectis/capabilities.py",
        "src/vectis/adapters/filesystem.py",
        "src/vectis/adapters/process.py",
    ),
    "DX-001": (
        "src/vectis/runtime.py",
        "src/vectis/compiler.py",
        "src/vectis/parser.py",
        "src/vectis/semantic.py",
        "pyproject.toml",
    ),
    "DX-002": (
        "src/vectis/cli.py",
        "src/vectis/runtime.py",
        "src/vectis/compiler.py",
        "src/vectis/parser.py",
        "src/vectis/semantic.py",
    ),
    "QA-001": (
        "src/vectis/cli.py",
        "src/vectis/runtime.py",
        "src/vectis/compiler.py",
        "src/vectis/semantic.py",
        "src/vectis/ir.py",
    ),
    "QA-002": (
        "src/vectis/runtime.py",
        "src/vectis/capabilities.py",
        "src/vectis/adapters/filesystem.py",
        "src/vectis/adapters/process.py",
        "src/vectis/adapters/http.py",
    ),
    "UX-001": (
        "src/vectis/diagnostic.py",
        "src/vectis/cli.py",
        "docs/design/diagnostics.md",
    ),
    "UX-002": (
        "src/vectis/cli.py",
        "docs/design/usability.md",
        "docs/design/error-message-guidelines.md",
    ),
    "DOC-001": (
        "src/vectis/cli.py",
        "src/vectis/runtime.py",
        "src/vectis/compiler.py",
        "README.md",
    ),
    "DOC-002": (
        "src/vectis/compiler.py",
        "src/vectis/ir.py",
        "src/vectis/runtime.py",
        "src/vectis/capabilities.py",
    ),
    "SUB-001": (
        "src/vectis/cli.py",
        "src/vectis/runtime.py",
        "src/vectis/compiler.py",
        "README.md",
    ),
    "SUB-002": (
        "README.md",
        "docs/demo.md",
        "examples/demo.vectis",
    ),
    "FINAL-001": (
        "README.md",
        "pyproject.toml",
        "src/vectis/__init__.py",
    ),
}


def _is_failure_line(line: str) -> bool:
    import re

    lowered = line.lower()

    phrase_markers = (
        "runtime module import failures",
        "missing required artifact",
        "missing required concept",
        "missing symbol",
        "requires at least",
        "error compiling",
        "traceback (most recent call last)",
        "no such file or directory",
        "rejected by",
        "failed to import test module",
    )

    if any(marker in lowered for marker in phrase_markers):
        return True

    exception_markers = (
        "ImportError:",
        "ModuleNotFoundError:",
        "SyntaxError:",
        "AssertionError:",
        "AttributeError:",
        "NameError:",
        "TypeError:",
        "ValueError:",
        "RuntimeError:",
    )

    if any(marker in line for marker in exception_markers):
        return True

    if re.search(
        r"^\s*File\s+[\"'][^\"']+\.py[\"'],\s+line\s+\d+",
        line,
    ):
        return True

    if (
        str(ROOT) in line
        and (
            ".py" in line
            or ".md" in line
        )
    ):
        return True

    if re.search(
        r"(^|[\s:])(?:ERROR|FAIL|FAILED)(?:[\s:/(]|$)",
        line,
    ):
        return True

    if line.startswith("E   "):
        return True

    return False

def compact_gate_output(
    output: str,
    *,
    limit: int = SPECIALIST_FAILURE_CONTEXT_MAX,
) -> str:
    # Keep deterministic failure evidence, not pages of successful tests.
    if not output:
        return ""

    lines = output.splitlines()
    matches = [
        index
        for index, line in enumerate(lines)
        if _is_failure_line(line)
    ]

    if not matches:
        compact = output[-limit:]
        return compact.strip()

    wanted: set[int] = set()

    for index in matches:
        for offset in range(-2, 4):
            candidate = index + offset

            if 0 <= candidate < len(lines):
                wanted.add(candidate)

    selected = [
        lines[index]
        for index in sorted(wanted)
    ]

    compact = "\n".join(selected).strip()

    if len(compact) > limit:
        compact = compact[-limit:]

    return compact


def compact_failure_evidence(
    state: dict[str, Any],
) -> str:
    feedback = str(
        state.get(
            "last_feedback",
            "",
        )
        or ""
    )

    quality = str(
        state.get(
            "last_quality_output",
            "",
        )
        or ""
    )

    pieces = []

    for value in (feedback, quality):
        compact = compact_gate_output(
            value
        )

        if compact and compact not in pieces:
            pieces.append(compact)

    if not pieces:
        return "(none)"

    combined = "\n\n".join(pieces)

    if len(combined) > SPECIALIST_FAILURE_CONTEXT_MAX:
        combined = combined[-SPECIALIST_FAILURE_CONTEXT_MAX:]

    return combined


def compact_repository_context() -> str:
    raw = repository_context()

    if len(raw) <= SPECIALIST_REPOSITORY_CONTEXT_MAX:
        return raw

    half = SPECIALIST_REPOSITORY_CONTEXT_MAX // 2

    return (
        raw[:half]
        + "\n...[repository context compacted]...\n"
        + raw[-half:]
    )


def _python_public_surface(
    source_path: pathlib.Path,
) -> str:
    import ast as py_ast

    try:
        source = source_path.read_text(
            encoding="utf-8"
        )
        tree = py_ast.parse(
            source,
            filename=str(source_path),
        )
    except (OSError, SyntaxError):
        return ""

    rendered: list[str] = []

    for node in tree.body:
        if isinstance(
            node,
            py_ast.ImportFrom,
        ):
            module = node.module or ""

            if module.startswith("vectis"):
                names = ", ".join(
                    alias.name
                    for alias in node.names
                )
                rendered.append(
                    f"from {module} import {names}"
                )

        elif isinstance(
            node,
            py_ast.ClassDef,
        ):
            bases = ", ".join(
                py_ast.unparse(base)
                for base in node.bases
            )

            header = (
                f"class {node.name}"
                + (f"({bases})" if bases else "")
                + ":"
            )
            rendered.append(header)

            for child in node.body:
                if isinstance(
                    child,
                    py_ast.AnnAssign,
                ) and isinstance(
                    child.target,
                    py_ast.Name,
                ):
                    field = (
                        "    "
                        + child.target.id
                        + ": "
                        + py_ast.unparse(
                            child.annotation
                        )
                    )

                    if child.value is not None:
                        field += (
                            " = "
                            + py_ast.unparse(
                                child.value
                            )
                        )

                    rendered.append(field)

                elif isinstance(
                    child,
                    py_ast.Assign,
                ):
                    names = [
                        target.id
                        for target in child.targets
                        if isinstance(
                            target,
                            py_ast.Name,
                        )
                    ]

                    for name in names:
                        if not name.startswith("_"):
                            rendered.append(
                                "    "
                                + name
                                + " = "
                                + py_ast.unparse(
                                    child.value
                                )
                            )

                elif isinstance(
                    child,
                    (
                        py_ast.FunctionDef,
                        py_ast.AsyncFunctionDef,
                    ),
                ):
                    if child.name.startswith("_"):
                        continue

                    signature = (
                        "    def "
                        + child.name
                        + "("
                        + py_ast.unparse(
                            child.args
                        )
                        + ")"
                    )

                    if child.returns is not None:
                        signature += (
                            " -> "
                            + py_ast.unparse(
                                child.returns
                            )
                        )

                    rendered.append(
                        signature + ": ..."
                    )

        elif isinstance(
            node,
            (
                py_ast.FunctionDef,
                py_ast.AsyncFunctionDef,
            ),
        ):
            if node.name.startswith("_"):
                continue

            signature = (
                "def "
                + node.name
                + "("
                + py_ast.unparse(
                    node.args
                )
                + ")"
            )

            if node.returns is not None:
                signature += (
                    " -> "
                    + py_ast.unparse(
                        node.returns
                    )
                )

            rendered.append(
                signature + ": ..."
            )

    return "\n".join(rendered)


def authoritative_dependency_context(
    task_id: str,
    target: str,
) -> str:
    # Exact project files outrank prose and model assumptions.
    spec = TASK_SPECS.get(
        task_id,
        {},
    )

    candidates: list[str] = [
        target,
    ]

    for relative in spec.get(
        "required_files",
        [],
    ):
        if relative not in candidates:
            candidates.append(relative)

    for relative in TASK_AUTHORITY_FILES.get(
        task_id,
        (),
    ):
        if relative not in candidates:
            candidates.append(relative)

    sections: list[str] = [
        (
            "AUTHORITY ORDER:\n"
            "1. Current checked-in Python source and normative grammar.\n"
            "2. Current task contract and existing task artifacts.\n"
            "3. Design/spec prose.\n"
            "4. Model assumptions.\n\n"
            "Never import, instantiate, or reference a project symbol "
            "unless the authoritative source below proves that symbol "
            "exists. Do not invent AST nodes, capabilities, declarations, "
            "or syntax to satisfy prose. If prose describes a future "
            "construct that the current AST/grammar cannot represent, "
            "implement only the semantics expressible by the current "
            "language and document the limitation."
        )
    ]

    used = len(sections[0])

    for relative in candidates:
        candidate = ROOT / relative

        if not candidate.is_file():
            continue

        try:
            content = candidate.read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeDecodeError):
            continue

        per_file_limit = (
            12_000
            if relative == target
            else 6_000
        )

        if len(content) > per_file_limit:
            content = (
                content[:per_file_limit]
                + "\n...[file compacted]...\n"
            )

        section = (
            "\n\n===== AUTHORITATIVE FILE: "
            + relative
            + " =====\n"
            + content
        )

        if (
            used + len(section)
            > SPECIALIST_AUTHORITY_CONTEXT_MAX
        ):
            continue

        sections.append(section)
        used += len(section)

    surfaces: list[str] = []

    src_root = ROOT / "src/vectis"

    if src_root.is_dir():
        for source_path in sorted(
            src_root.glob("*.py")
        ):
            surface = _python_public_surface(
                source_path
            )

            if not surface:
                continue

            surfaces.append(
                "\n### "
                + source_path.relative_to(
                    ROOT
                ).as_posix()
                + "\n"
                + surface
            )

    if surfaces:
        surface_section = (
            "\n\n===== CANONICAL PYTHON API SURFACE ====="
            + "".join(surfaces)
        )

        remaining = (
            SPECIALIST_AUTHORITY_CONTEXT_MAX
            - used
        )

        if remaining > 1_000:
            sections.append(
                surface_section[:remaining]
            )

    return "".join(sections)

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

DETERMINISTIC FAILURE / REVIEW EVIDENCE:
{compact_failure_evidence(state)}

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

COMPACT PROJECT CONTEXT:
{compact_repository_context()}

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



def snapshot_proposal_files(
    proposal: dict[str, Any],
) -> dict[str, bytes | None]:
    snapshot: dict[str, bytes | None] = {}

    for file in proposal["files"]:
        relative = validate_path(
            file["path"]
        ).as_posix()

        target = ROOT / relative

        snapshot[relative] = (
            target.read_bytes()
            if target.is_file()
            else None
        )

    return snapshot


def restore_proposal_snapshot(
    snapshot: dict[str, bytes | None],
) -> None:
    for relative, content in snapshot.items():
        target = ROOT / validate_path(
            relative
        )

        if content is None:
            if target.exists():
                if not target.is_file():
                    raise RuntimeError(
                        "Refusing to remove non-file proposal target: "
                        + relative
                    )

                target.unlink()

            continue

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_bytes(
            content
        )


def task_gate_reports_incomplete(
    output: str,
) -> bool:
    return (
        "missing required artifact:"
        in output.lower()
    )



def quality_failure_fingerprint(
    output: str,
) -> str:
    import re

    retained = []

    for line in output.splitlines():
        if not _is_failure_line(
            line
        ):
            continue

        normalized = line.strip()

        normalized = re.sub(
            r"\bline\s+\d+\b",
            "line #",
            normalized,
        )

        normalized = re.sub(
            r"\b0x[0-9a-fA-F]+\b",
            "0x#",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        retained.append(
            normalized
        )

    return "\n".join(
        retained
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


def task_gate(
    task_id: str,
) -> tuple[bool, str]:
    """Run deterministic acceptance checks for one task."""
    result = run(
        [
            "bash",
            "tools/task-gates/run-task-gate.sh",
            task_id,
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
                ] = compact_gate_output(output)

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

        try:
            validate_task_contract(
                task["id"]
            )
        except Exception as exc:
            log(
                "TASK CONTRACT BLOCK // "
                + task["id"]
                + " // "
                + type(exc).__name__
                + ": "
                + str(exc)
            )
            return 2

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

        proposal_snapshot: dict[str, bytes | None] | None = None

        try:
            selected_target = next_task_target(
                task["id"],
                state,
            )

            proposal = generate_parsed(
                model,
                specialist_transport_prompt(
                    task,
                    role,
                    state,
                    target=selected_target,
                ),
                lambda raw: parse_specialist_transport(
                    raw,
                    selected_target,
                ),
                f"{task['id']} specialist",
                json_mode=False,
            )

            if not proposal["files"]:
                raise RuntimeError(
                    "Specialist returned no files."
                )

            validate_specialist_target(
                task["id"],
                state,
                proposal,
            )

            validate_task_file_boundary(
                task["id"],
                proposal,
            )

            proposal_snapshot = snapshot_proposal_files(
                proposal
            )

            apply_change(
                proposal
            )

            passed, quality_output = (
                quality_gate()
            )

            state[
                "last_quality_output"
            ] = compact_gate_output(quality_output)

            if not passed:
                current_compact = compact_gate_output(
                    quality_output
                )

                failure_target = failure_target_from_evidence(
                    task["id"],
                    quality_output,
                )

                task_local_failure = (
                    failure_target
                    in TASK_FILE_RULES.get(
                        task["id"],
                        set(),
                    )
                )

                previous_fingerprint = quality_failure_fingerprint(
                    str(
                        state.get(
                            "last_quality_output",
                            "",
                        )
                    )
                )

                current_fingerprint = quality_failure_fingerprint(
                    current_compact
                )

                if task_local_failure:
                    # Keep the newly generated, syntax-valid task artifact.
                    # A subsequent iteration can repair the next latent error
                    # instead of restarting from the old snapshot.
                    proposal_snapshot = None

                    if (
                        current_fingerprint
                        and current_fingerprint
                        != previous_fingerprint
                    ):
                        # The existing increment below turns -1 into 0,
                        # resetting the budget after real forward progress.
                        state["repair_failures"] = -1
                else:
                    # Protected regression outside the current task:
                    # restore only this proposal, never all staged WIP.
                    if proposal_snapshot is not None:
                        restore_proposal_snapshot(
                            proposal_snapshot
                        )
                        proposal_snapshot = None

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

            task_passed, task_output = task_gate(
                task["id"]
            )

            if (
                not task_passed
                and task_gate_reports_incomplete(
                    task_output
                )
            ):
                state["repair_failures"] = 0
                state["last_quality_output"] = (
                    compact_gate_output(
                        task_output
                    )
                )
                state["last_feedback"] = (
                    "The current staged artifact passed the global "
                    "quality gate. The task is incomplete because a "
                    "required artifact is still missing. Preserve all "
                    "globally-green task WIP and create only the next "
                    "missing required artifact in manifest order."
                )

                save_state(
                    state
                )

                log(
                    f"{task['id']} staged artifact accepted; "
                    "continuing to next required artifact."
                )

                proposal_snapshot = None

                time.sleep(
                    LOOP_DELAY
                )

                continue

            if not task_passed:
                proposal_snapshot = None

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
                    "last_quality_output"
                ] = compact_gate_output(task_output)

                state[
                    "last_feedback"
                ] = (
                    "Deterministic task acceptance gate failed. "
                    "Repair only the task-specific contract based "
                    "on the evidence below.\n\n"
                    + compact_gate_output(task_output)
                )

                save_state(
                    state
                )

                log(
                    f"{task['id']} task-gate failure "
                    f"{state['repair_failures']}/"
                    f"{MAX_REPAIR_FAILURES}"
                )

                if (
                    state["repair_failures"]
                    >= MAX_REPAIR_FAILURES
                ):
                    diagnostic = (
                        compact_gate_output(task_output)
                    )

                    state[
                        "repair_failures"
                    ] = 0

                    state[
                        "last_feedback"
                    ] = (
                        "The previous candidate was rolled back "
                        "to the last green commit after repeated "
                        "deterministic task-gate failures. "
                        "Preserve completed-task behavior and "
                        "repair only the current task contract.\n\n"
                        "LAST TASK-GATE EVIDENCE:\n"
                        + diagnostic
                    )

                    save_state(
                        state
                    )

                    log(
                        "Repeated task-gate failure threshold "
                        "reached; returned to last green commit."
                    )

                time.sleep(
                    LOOP_DELAY
                )

                continue

            proposal_snapshot = None

            review_evidence = (
                quality_output
                + "\n\n"
                + task_output
            )

            review = generate_parsed(
                model,
                reviewer_prompt(
                    task,
                    reviewer,
                    review_evidence,
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

            proposal_snapshot = None

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
            if proposal_snapshot is not None:
                restore_proposal_snapshot(
                    proposal_snapshot
                )
                proposal_snapshot = None

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
                    "preserved staged task WIP."
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
