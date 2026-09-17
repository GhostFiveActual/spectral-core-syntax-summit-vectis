"""VECTIS command-line interface."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from vectis import __version__
from vectis.compiler import CompileResult, compile_program
from vectis.lexer import LexerError
from vectis.parser import ParserError, parse
from vectis.runtime import Runtime


def _jsonable(value: Any) -> Any:
    """Convert VECTIS public data structures into JSON-compatible values."""
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
        return [
            _jsonable(item)
            for item in value
        ]

    return value


def _read_source(source: str) -> tuple[str, str]:
    """Read a source file or standard input."""
    if source == "-":
        return sys.stdin.read(), "<stdin>"

    path = Path(source)
    return path.read_text(encoding="utf-8"), str(path)


def _print_diagnostics(result: CompileResult) -> None:
    for diagnostic in result.diagnostics:
        print(str(diagnostic), file=sys.stderr)


def _compile_source(source: str):
    text, file = _read_source(source)
    program = parse(text, file=file)
    result = compile_program(program)

    if result.graph is None or result.diagnostics:
        _print_diagnostics(result)
        return None

    return result.graph


def command_check(args: argparse.Namespace) -> int:
    """Validate syntax and semantics without executing the program."""
    graph = _compile_source(args.source)

    if graph is None:
        return 1

    print("OK")
    return 0


def command_parse(args: argparse.Namespace) -> int:
    """Parse VECTIS source and emit deterministic JSON AST data."""
    text, file = _read_source(args.source)
    program = parse(text, file=file)

    print(
        json.dumps(
            _jsonable(program),
            indent=2,
            sort_keys=True,
        )
    )

    return 0


def command_plan(args: argparse.Namespace) -> int:
    """Compile VECTIS source and emit its deterministic execution graph."""
    graph = _compile_source(args.source)

    if graph is None:
        return 1

    print(graph.to_json())
    return 0


def command_run(args: argparse.Namespace) -> int:
    """Compile and execute a VECTIS program."""
    graph = _compile_source(args.source)

    if graph is None:
        return 1

    result = Runtime(
        graph,
        dry_run=args.dry_run,
    ).execute()

    print(
        json.dumps(
            _jsonable(result),
            indent=2,
            sort_keys=True,
        )
    )

    return 0 if result.success else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vectis",
        description=(
            "VECTIS deterministic language toolchain"
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

    def source_argument(
        command: argparse.ArgumentParser,
    ) -> None:
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

    check_parser = commands.add_parser(
        "check",
        help="validate VECTIS syntax and semantics",
        description=(
            "Validate VECTIS syntax and semantics "
            "without executing the program."
        ),
    )
    source_argument(check_parser)
    check_parser.set_defaults(handler=command_check)

    parse_parser = commands.add_parser(
        "parse",
        help="parse source and print its AST as JSON",
        description=(
            "Parse VECTIS source and print deterministic "
            "JSON AST data."
        ),
    )
    source_argument(parse_parser)
    parse_parser.set_defaults(handler=command_parse)

    plan_parser = commands.add_parser(
        "plan",
        help="compile source into an execution graph",
        description=(
            "Compile VECTIS source and print the "
            "deterministic execution graph."
        ),
    )
    source_argument(plan_parser)
    plan_parser.set_defaults(handler=command_plan)

    run_parser = commands.add_parser(
        "run",
        help="compile and execute VECTIS source",
        description=(
            "Compile and execute a VECTIS program."
        ),
    )
    source_argument(run_parser)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "produce deterministic runtime states "
            "without invoking node handlers"
        ),
    )
    run_parser.set_defaults(handler=command_run)

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
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
    except (OSError, UnicodeError) as exc:
        print(f"vectis: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
