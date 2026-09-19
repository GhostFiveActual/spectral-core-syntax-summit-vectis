"""VECTIS command-line interface."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
import platform
import sys
from typing import Any, Sequence

from vectis import __version__
from vectis.capabilities import Capability, CapabilityRegistry
from vectis.compiler import CompileResult, compile_program
from vectis.evaluator import builtin_manifest
from vectis.formatter import format_program
from vectis.lexer import Lexer, LexerError
from vectis.parser import ParserError, parse
from vectis.runtime import Runtime


_CAPABILITY_DESCRIPTIONS = {
    "filesystem": "Controlled filesystem adapter boundary.",
    "process": "Allowlisted structured process adapter boundary.",
    "http": "Bounded HTTP request adapter boundary.",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _read_source(source: str) -> tuple[str, str]:
    if source == "-":
        return sys.stdin.read(), "<stdin>"
    path = Path(source)
    return path.read_text(encoding="utf-8"), str(path)


def _print_json(value: object) -> None:
    print(json.dumps(_jsonable(value), indent=2, sort_keys=True))


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


def _capability_registry(names: Sequence[str]) -> CapabilityRegistry | None:
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
    graph = _compile_source(args.source)
    if graph is None:
        return 1
    print("OK")
    return 0


def command_tokens(args: argparse.Namespace) -> int:
    text, file = _read_source(args.source)
    _print_json(Lexer(text, file=file).tokenize())
    return 0


def command_parse(args: argparse.Namespace) -> int:
    text, file = _read_source(args.source)
    _print_json(parse(text, file=file))
    return 0


def command_plan(args: argparse.Namespace) -> int:
    graph = _compile_source(args.source)
    if graph is None:
        return 1
    print(graph.to_json())
    return 0


def command_inspect(args: argparse.Namespace) -> int:
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
    text, file = _read_source(args.source)
    formatted = format_program(parse(text, file=file))

    if args.check:
        if text == formatted:
            print("OK")
            return 0
        print(f"vectis: formatting required: {file}", file=sys.stderr)
        return 1

    if args.write:
        if args.source == "-":
            print("vectis: --write requires a file path", file=sys.stderr)
            return 2
        Path(args.source).write_text(formatted, encoding="utf-8")
        print(args.source)
        return 0

    sys.stdout.write(formatted)
    return 0


def command_builtins(_args: argparse.Namespace) -> int:
    _print_json({"builtins": builtin_manifest()})
    return 0


def command_capabilities(_args: argparse.Namespace) -> int:
    _print_json(
        {
            "capabilities": [
                {"name": name, "description": description}
                for name, description in sorted(
                    _CAPABILITY_DESCRIPTIONS.items()
                )
            ]
        }
    )
    return 0


def command_doctor(_args: argparse.Namespace) -> int:
    _print_json(
        {
            "vectis": __version__,
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "builtins": len(builtin_manifest()),
            "capabilities": sorted(_CAPABILITY_DESCRIPTIONS),
        }
    )
    return 0


def command_studio(args: argparse.Namespace) -> int:
    from vectis.studio import run_studio

    run_studio(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        allow_remote=args.allow_remote,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vectis",
        description="VECTIS deterministic language, runtime, and Studio toolchain",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="display the VECTIS version and exit",
    )

    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    def source_argument(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "source",
            nargs="?",
            default="-",
            metavar="FILE",
            help="VECTIS source file; use '-' or omit FILE to read standard input",
        )

    check_parser = commands.add_parser("check", help="validate syntax and semantics")
    source_argument(check_parser)
    check_parser.set_defaults(handler=command_check)

    tokens_parser = commands.add_parser("tokens", help="print the lexer token stream as JSON")
    source_argument(tokens_parser)
    tokens_parser.set_defaults(handler=command_tokens)

    parse_parser = commands.add_parser("parse", help="parse source and print its AST as JSON")
    source_argument(parse_parser)
    parse_parser.set_defaults(handler=command_parse)

    plan_parser = commands.add_parser("plan", help="compile source into an execution graph")
    source_argument(plan_parser)
    plan_parser.set_defaults(handler=command_plan)

    inspect_parser = commands.add_parser("inspect", help="show tokens, AST, diagnostics, and graph")
    source_argument(inspect_parser)
    inspect_parser.set_defaults(handler=command_inspect)

    run_parser = commands.add_parser("run", help="compile and execute VECTIS source")
    source_argument(run_parser)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="produce deterministic runtime states without invoking handlers",
    )
    run_parser.add_argument(
        "--capability",
        action="append",
        default=[],
        metavar="NAME",
        help="grant a named runtime capability; may be repeated",
    )
    run_parser.set_defaults(handler=command_run)

    fmt_parser = commands.add_parser("fmt", help="format VECTIS source canonically")
    source_argument(fmt_parser)
    mode = fmt_parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail when formatting differs")
    mode.add_argument("--write", action="store_true", help="rewrite the source file in place")
    fmt_parser.set_defaults(handler=command_fmt)

    builtins_parser = commands.add_parser("builtins", help="list deterministic built-in functions")
    builtins_parser.set_defaults(handler=command_builtins)

    capabilities_parser = commands.add_parser("capabilities", help="list standard capability names")
    capabilities_parser.set_defaults(handler=command_capabilities)

    doctor_parser = commands.add_parser("doctor", help="show local VECTIS environment information")
    doctor_parser.set_defaults(handler=command_doctor)

    for command_name in ("studio", "app"):
        studio_parser = commands.add_parser(
            command_name,
            help="launch the local VECTIS Studio UI",
        )
        studio_parser.add_argument("--host", default="127.0.0.1")
        studio_parser.add_argument("--port", type=int, default=8765)
        studio_parser.add_argument("--no-browser", action="store_true")
        studio_parser.add_argument(
            "--allow-remote",
            action="store_true",
            help="permit binding to a non-loopback interface",
        )
        studio_parser.set_defaults(handler=command_studio)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
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
