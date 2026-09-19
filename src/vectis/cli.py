# GHOST FIVE // SPECTRAL CORE // VECTIS
# Implements the VECTIS command line interface and command routing.
"""VECTIS command line interface."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any, Sequence

from vectis import __version__
from vectis.capabilities import Capability, CapabilityRegistry
from vectis.compiler import CompileResult, compile_program
from vectis.demo_app import run_demo_app
from vectis.evaluator import builtin_manifest, evaluate_expression
from vectis.examples import CANONICAL_EXAMPLES, example_manifest
from vectis.formatter import format_program
from vectis.lexer import Lexer, LexerError
from vectis.parser import ParserError, parse, parse_expression
from vectis.product import (
    graph_summary,
    graph_to_dot,
    graph_to_mermaid,
    initialize_project,
    test_project,
)
from vectis.runtime import Runtime


_CAPABILITY_DESCRIPTIONS = {
    "filesystem": "Controlled filesystem adapter boundary.",
    "process": "Allowlisted structured process adapter boundary.",
    "http": "Bounded HTTP request adapter boundary.",
}


def _jsonable(value: Any) -> Any:
    """Convert public VECTIS values into deterministic JSON safe data."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _jsonable(item)
            for key, item in asdict(value).items()
        }
    if isinstance(value, dict):
        return {
            str(key): _jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _read_source(source: str) -> tuple[str, str]:
    """Read source from a file path or standard input."""
    if source == "-":
        return sys.stdin.read(), "<stdin>"
    path = Path(source)
    return path.read_text(encoding="utf-8"), str(path)


def _print_json(value: object) -> None:
    """Print stable human readable JSON for CLI and script consumers."""
    print(
        json.dumps(
            _jsonable(value),
            indent=2,
            sort_keys=True,
        )
    )


def _print_diagnostics(result: CompileResult) -> None:
    """Render compiler diagnostics to standard error."""
    for diagnostic in result.diagnostics:
        print(str(diagnostic), file=sys.stderr)


def _compile_source(source: str):
    """Parse and compile one source input or return None after diagnostics."""
    text, file = _read_source(source)
    program = parse(text, file=file)
    result = compile_program(program)
    if result.graph is None or result.diagnostics:
        _print_diagnostics(result)
        return None
    return result.graph


def _capability_registry(
    names: Sequence[str],
) -> CapabilityRegistry | None:
    """Build an explicit runtime capability registry from CLI grants."""
    if not names:
        return None

    registry = CapabilityRegistry()
    for name in dict.fromkeys(names):
        registry.declare_capability(
            Capability(
                name=name,
                description=_CAPABILITY_DESCRIPTIONS.get(
                    name,
                    "Explicit CLI capability grant.",
                ),
            )
        )
    return registry


def command_check(args: argparse.Namespace) -> int:
    """Validate syntax and semantics without executing the mission."""
    graph = _compile_source(args.source)
    if graph is None:
        return 1
    print("OK")
    return 0


def command_tokens(args: argparse.Namespace) -> int:
    """Emit the deterministic token stream."""
    text, file = _read_source(args.source)
    _print_json(Lexer(text, file=file).tokenize())
    return 0


def command_parse(args: argparse.Namespace) -> int:
    """Emit the typed abstract syntax tree."""
    text, file = _read_source(args.source)
    _print_json(parse(text, file=file))
    return 0


def command_plan(args: argparse.Namespace) -> int:
    """Compile source and emit the execution graph as JSON."""
    graph = _compile_source(args.source)
    if graph is None:
        return 1
    print(graph.to_json())
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    """Emit tokens, syntax tree, diagnostics, and graph in one document."""
    text, file = _read_source(args.source)
    tokens = Lexer(text, file=file).tokenize()
    program = parse(text, file=file)
    result = compile_program(program)
    _print_json(
        {
            "version": __version__,
            "tokens": tokens,
            "ast": program,
            "diagnostics": result.diagnostics,
            "execution_graph": (
                result.graph.to_dict()
                if result.graph is not None
                else None
            ),
        }
    )
    return 0 if result.ok else 1


def command_run(args: argparse.Namespace) -> int:
    """Compile and execute one VECTIS mission."""
    graph = _compile_source(args.source)
    if graph is None:
        return 1

    result = Runtime(
        graph,
        dry_run=args.dry_run,
        capabilities=_capability_registry(args.capability),
    ).execute()
    _print_json(result)
    return 0 if result.success else 1


def command_fmt(args: argparse.Namespace) -> int:
    """Print, check, or write canonical VECTIS formatting."""
    text, file = _read_source(args.source)
    formatted = format_program(parse(text, file=file))

    if args.check:
        if text == formatted:
            print("OK")
            return 0
        print(
            f"vectis: formatting required: {file}",
            file=sys.stderr,
        )
        return 1

    if args.write:
        if args.source == "-":
            print(
                "vectis: --write requires a file path",
                file=sys.stderr,
            )
            return 2
        Path(args.source).write_text(
            formatted,
            encoding="utf-8",
        )
        print(args.source)
        return 0

    sys.stdout.write(formatted)
    return 0


def command_builtins(_args: argparse.Namespace) -> int:
    """List the deterministic built in function registry."""
    _print_json({"builtins": builtin_manifest()})
    return 0


def command_capabilities(_args: argparse.Namespace) -> int:
    """List standard VECTIS capability names."""
    _print_json(
        {
            "capabilities": [
                {
                    "name": name,
                    "description": description,
                }
                for name, description in sorted(
                    _CAPABILITY_DESCRIPTIONS.items()
                )
            ]
        }
    )
    return 0


def command_doctor(_args: argparse.Namespace) -> int:
    """Report the local VECTIS runtime environment."""
    _print_json(
        {
            "vectis": __version__,
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "builtins": len(builtin_manifest()),
            "capabilities": sorted(
                _CAPABILITY_DESCRIPTIONS
            ),
        }
    )
    return 0


def command_eval(args: argparse.Namespace) -> int:
    """Evaluate a pure VECTIS expression from the command line."""
    value = evaluate_expression(
        parse_expression(
            args.expression,
            file="<cli-expression>",
        ),
        {},
    )
    _print_json(
        {
            "expression": args.expression,
            "value": value,
        }
    )
    return 0


def command_graph(args: argparse.Namespace) -> int:
    """Export a compiled graph in JSON, DOT, or Mermaid form."""
    graph = _compile_source(args.source)
    if graph is None:
        return 1

    if args.format == "json":
        print(graph.to_json())
    elif args.format == "dot":
        sys.stdout.write(graph_to_dot(graph))
    else:
        sys.stdout.write(graph_to_mermaid(graph))
    return 0


def command_explain(args: argparse.Namespace) -> int:
    """Explain the structural shape of a compiled mission."""
    graph = _compile_source(args.source)
    if graph is None:
        return 1

    _print_json(
        {
            "source": args.source,
            "summary": graph_summary(graph),
        }
    )
    return 0


def command_init(args: argparse.Namespace) -> int:
    """Create a Ghost Five branded VECTIS project scaffold."""
    created = initialize_project(
        Path(args.path),
        force=args.force,
    )
    _print_json(
        {
            "root": str(Path(args.path).resolve()),
            "created": [
                str(path)
                for path in created
            ],
        }
    )
    return 0


def command_test(args: argparse.Namespace) -> int:
    """Compile every VECTIS source file below a project path."""
    result = test_project(Path(args.path))
    _print_json(result)
    return 0 if result["failed"] == 0 else 1


def command_examples(args: argparse.Namespace) -> int:
    """List or print the canonical VECTIS examples."""
    if args.name is None:
        _print_json(
            {
                "examples": example_manifest(),
            }
        )
        return 0

    source = CANONICAL_EXAMPLES.get(args.name)
    if source is None:
        print(
            f"vectis: unknown example {args.name!r}",
            file=sys.stderr,
        )
        return 2

    sys.stdout.write(source)
    return 0


def command_repl(_args: argparse.Namespace) -> int:
    """Run a small deterministic expression REPL with local scalar variables."""
    values: dict[str, object] = {}
    assignment = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?!=)(.+)$"
    )

    print(
        "VECTIS REPL // :quit exits // :vars prints variables"
    )

    while True:
        try:
            line = input("vectis> ").strip()
        except EOFError:
            print()
            return 0

        if not line:
            continue
        if line in {":quit", ":exit"}:
            return 0
        if line == ":vars":
            _print_json(values)
            continue

        match = assignment.match(line)
        expression_text = line
        target = None

        if match is not None:
            target = match.group(1)
            expression_text = match.group(2).strip()

        try:
            value = evaluate_expression(
                parse_expression(
                    expression_text,
                    file="<repl>",
                ),
                values,
            )
        except Exception as exc:
            print(
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            continue

        if target is not None:
            values[target] = value
            print(f"{target} = {json.dumps(value)}")
        else:
            _print_json(value)


def command_studio(args: argparse.Namespace) -> int:
    """Launch the local VECTIS Studio workbench."""
    from vectis.studio import run_studio

    run_studio(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        allow_remote=args.allow_remote,
    )
    return 0


def command_demo(args: argparse.Namespace) -> int:
    """Launch the Mission Readiness application powered by VECTIS."""
    run_demo_app(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        allow_remote=args.allow_remote,
    )
    return 0


def command_version(_args: argparse.Namespace) -> int:
    """Print only the installed VECTIS version."""
    print(__version__)
    return 0


def _add_source_argument(
    command: argparse.ArgumentParser,
) -> None:
    """Add the standard VECTIS source file argument to a parser."""
    command.add_argument(
        "source",
        nargs="?",
        default="-",
        metavar="FILE",
        help=(
            "VECTIS source file; use '-' or omit FILE "
            "to read standard input"
        ),
    )


def _add_server_arguments(
    command: argparse.ArgumentParser,
    *,
    default_port: int,
) -> None:
    """Add common local application server arguments."""
    command.add_argument(
        "--host",
        default="127.0.0.1",
    )
    command.add_argument(
        "--port",
        type=int,
        default=default_port,
    )
    command.add_argument(
        "--no-browser",
        action="store_true",
    )
    command.add_argument(
        "--allow-remote",
        action="store_true",
        help=(
            "permit binding to a non-loopback interface"
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the complete VECTIS command line grammar."""
    parser = argparse.ArgumentParser(
        prog="vectis",
        description=(
            "VECTIS deterministic language, runtime, and Studio toolchain. "
            "Ghost Five // Spectral Core project and application commands."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="display the VECTIS version and exit",
    )

    commands = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    check_parser = commands.add_parser(
        "check",
        help="validate syntax and semantics",
    )
    _add_source_argument(check_parser)
    check_parser.set_defaults(handler=command_check)

    tokens_parser = commands.add_parser(
        "tokens",
        help="print the lexer token stream as JSON",
    )
    _add_source_argument(tokens_parser)
    tokens_parser.set_defaults(handler=command_tokens)

    parse_parser = commands.add_parser(
        "parse",
        help="parse source and print its AST as JSON",
    )
    _add_source_argument(parse_parser)
    parse_parser.set_defaults(handler=command_parse)

    plan_parser = commands.add_parser(
        "plan",
        help="compile source into an execution graph",
    )
    _add_source_argument(plan_parser)
    plan_parser.set_defaults(handler=command_plan)

    inspect_parser = commands.add_parser(
        "inspect",
        help="show tokens, AST, diagnostics, and graph",
    )
    _add_source_argument(inspect_parser)
    inspect_parser.set_defaults(handler=command_inspect)

    run_parser = commands.add_parser(
        "run",
        help="compile and execute VECTIS source",
    )
    _add_source_argument(run_parser)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "produce deterministic runtime states without "
            "invoking handlers"
        ),
    )
    run_parser.add_argument(
        "--capability",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "grant a named runtime capability; may be repeated"
        ),
    )
    run_parser.set_defaults(handler=command_run)

    fmt_parser = commands.add_parser(
        "fmt",
        help="format VECTIS source canonically",
    )
    _add_source_argument(fmt_parser)
    mode = fmt_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail when formatting differs",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="rewrite the source file in place",
    )
    fmt_parser.set_defaults(handler=command_fmt)

    eval_parser = commands.add_parser(
        "eval",
        help="evaluate one pure VECTIS expression",
    )
    eval_parser.add_argument(
        "expression",
        help="VECTIS expression to evaluate",
    )
    eval_parser.set_defaults(handler=command_eval)

    graph_parser = commands.add_parser(
        "graph",
        help="export the execution graph",
    )
    _add_source_argument(graph_parser)
    graph_parser.add_argument(
        "--format",
        choices=("json", "dot", "mermaid"),
        default="json",
        help="graph output format",
    )
    graph_parser.set_defaults(handler=command_graph)

    explain_parser = commands.add_parser(
        "explain",
        help="summarize a compiled mission",
    )
    _add_source_argument(explain_parser)
    explain_parser.set_defaults(handler=command_explain)

    init_parser = commands.add_parser(
        "init",
        aliases=["new"],
        help="create a Ghost Five branded VECTIS project",
    )
    init_parser.add_argument(
        "path",
        nargs="?",
        default=".",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="replace scaffold files that already exist",
    )
    init_parser.set_defaults(handler=command_init)

    test_parser = commands.add_parser(
        "test",
        help="compile every VECTIS file under a path",
    )
    test_parser.add_argument(
        "path",
        nargs="?",
        default=".",
    )
    test_parser.set_defaults(handler=command_test)

    examples_parser = commands.add_parser(
        "examples",
        help="list or print canonical VECTIS examples",
    )
    examples_parser.add_argument(
        "name",
        nargs="?",
    )
    examples_parser.set_defaults(handler=command_examples)

    repl_parser = commands.add_parser(
        "repl",
        help="open the deterministic expression REPL",
    )
    repl_parser.set_defaults(handler=command_repl)

    builtins_parser = commands.add_parser(
        "builtins",
        help="list deterministic built in functions",
    )
    builtins_parser.set_defaults(handler=command_builtins)

    capabilities_parser = commands.add_parser(
        "capabilities",
        help="list standard capability names",
    )
    capabilities_parser.set_defaults(
        handler=command_capabilities
    )

    doctor_parser = commands.add_parser(
        "doctor",
        help="show local VECTIS environment information",
    )
    doctor_parser.set_defaults(handler=command_doctor)

    version_parser = commands.add_parser(
        "version",
        help="print the installed VECTIS version",
    )
    version_parser.set_defaults(handler=command_version)

    for command_name in ("studio", "app"):
        studio_parser = commands.add_parser(
            command_name,
            help="launch the local VECTIS Studio UI",
        )
        _add_server_arguments(
            studio_parser,
            default_port=8765,
        )
        studio_parser.set_defaults(handler=command_studio)

    demo_parser = commands.add_parser(
        "demo",
        aliases=["showcase"],
        help="launch the VECTIS Mission Readiness demo",
    )
    _add_server_arguments(
        demo_parser,
        default_port=8775,
    )
    demo_parser.set_defaults(handler=command_demo)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the VECTIS CLI and normalize user facing failures."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)

    if handler is None:
        parser.print_help()
        return 0

    try:
        return int(handler(args))
    except (LexerError, ParserError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"vectis: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
