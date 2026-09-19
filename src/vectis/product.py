# GHOST FIVE // SPECTRAL CORE // VECTIS
# Provides project scaffolding, graph exports, expression tools, and batch validation.

from __future__ import annotations

from collections import Counter
from pathlib import Path
import json

from vectis.compiler import compile_program
from vectis.evaluator import Scalar, evaluate_expression
from vectis.ir import EdgeKind, ExecutionGraph
from vectis.parser import parse, parse_expression


BRAND_BLOCK = """<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->
"""


def evaluate_text(expression: str) -> Scalar:
    """Evaluate one pure VECTIS expression without creating a mission."""
    return evaluate_expression(
        parse_expression(expression, file="<cli-expression>"),
        {},
    )


def graph_summary(graph: ExecutionGraph) -> dict[str, object]:
    """Return a stable summary suitable for CLI and application output."""
    kinds = Counter(node.kind.value for node in graph.nodes)
    branch_edges = sum(
        1
        for edge in graph.edges
        if edge.kind in (EdgeKind.TRUE_BRANCH, EdgeKind.FALSE_BRANCH)
    )
    return {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "branch_edges": branch_edges,
        "node_kinds": dict(sorted(kinds.items())),
        "topological_order": list(graph.topological_order()),
    }


def graph_to_dot(graph: ExecutionGraph) -> str:
    """Render an execution graph as Graphviz DOT without external packages."""
    lines = ["digraph vectis {", "  rankdir=LR;"]
    for node in graph.nodes:
        label = f"{node.id}\\n{node.kind.value}"
        lines.append(
            f"  {json.dumps(node.id)} "
            f"[label={json.dumps(label)}];"
        )
    for edge in graph.edges:
        lines.append(
            f"  {json.dumps(edge.source)} -> "
            f"{json.dumps(edge.target)} "
            f"[label={json.dumps(edge.kind.value)}];"
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def graph_to_mermaid(graph: ExecutionGraph) -> str:
    """Render an execution graph as Mermaid flowchart text."""
    lines = ["flowchart LR"]
    for node in graph.nodes:
        safe_id = _mermaid_id(node.id)
        label = f"{node.id} | {node.kind.value}".replace('"', "'")
        lines.append(f'    {safe_id}["{label}"]')
    for edge in graph.edges:
        lines.append(
            f"    {_mermaid_id(edge.source)} "
            f"-->|{edge.kind.value}| "
            f"{_mermaid_id(edge.target)}"
        )
    return "\n".join(lines) + "\n"


def _mermaid_id(value: str) -> str:
    """Convert a graph node identifier into a Mermaid safe identifier."""
    return "n_" + "".join(
        char if char.isalnum() else "_"
        for char in value
    )


def initialize_project(root: Path, *, force: bool = False) -> tuple[Path, ...]:
    """Create a small Ghost Five branded VECTIS project scaffold."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    files = {
        root / "README.md": (
            BRAND_BLOCK
            + "\n# VECTIS Project\n\n"
            + "## Purpose\n\n"
            + "This project was created with vectis init. "
            + "Put executable missions in the missions directory and "
            + "validate them with vectis test.\n"
        ),
        root / "vectis.toml": (
            "# GHOST FIVE // SPECTRAL CORE // VECTIS\n"
            "# Project metadata for a VECTIS mission collection.\n"
            "[project]\n"
            'name = "vectis-project"\n'
            'mission_root = "missions"\n'
        ),
        root / "missions" / "main.vectis": (
            "// GHOST FIVE // SPECTRAL CORE // VECTIS\n"
            "// Primary mission created by vectis init.\n"
            'mission "Primary mission" {\n'
            "    source ready true;\n"
            '    let status if_else(ready, "READY", "REVIEW");\n'
            "\n"
            "    when ready {\n"
            "        publish status;\n"
            "    } otherwise {\n"
            '        request "manual-review";\n'
            "    }\n"
            "}\n"
        ),
    }

    created: list[Path] = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            raise FileExistsError(
                f"{path} already exists; use --force to replace scaffold files"
            )
        path.write_text(content, encoding="utf-8")
        created.append(path)

    return tuple(created)


def test_project(root: Path) -> dict[str, object]:
    """Compile every VECTIS file below a path and return deterministic results."""
    root = root.resolve()
    paths = (
        [root]
        if root.is_file()
        else sorted(root.rglob("*.vectis"))
    )

    records: list[dict[str, object]] = []
    passed = 0

    for path in paths:
        try:
            program = parse(
                path.read_text(encoding="utf-8"),
                file=str(path),
            )
            result = compile_program(program)
            ok = result.ok
            diagnostics = [
                diagnostic.to_dict()
                for diagnostic in result.diagnostics
            ]
        except Exception as exc:
            ok = False
            diagnostic = getattr(exc, "diagnostic", None)
            diagnostics = (
                [diagnostic.to_dict()]
                if diagnostic is not None
                else [{"message": f"{type(exc).__name__}: {exc}"}]
            )

        if ok:
            passed += 1

        records.append(
            {
                "file": str(path),
                "ok": ok,
                "diagnostics": diagnostics,
            }
        )

    return {
        "root": str(root),
        "files": len(records),
        "passed": passed,
        "failed": len(records) - passed,
        "results": records,
    }
