# VECTIS CLI Toolchain

## Purpose

The `vectis` command provides the local command-line interface for the deterministic VECTIS language pipeline.

The console entry point remains:

```text
vectis = "vectis.cli:main"
```

## Commands

The CLI exposes four explicit toolchain commands:

- `vectis check`
- `vectis parse`
- `vectis plan`
- `vectis run`

Each command accepts a VECTIS source file. If the file argument is omitted, or `-` is used, source is read from standard input.

## `vectis check`

`vectis check FILE` parses and semantically compiles a program without executing it.

A valid program prints `OK` and exits successfully. Syntax or semantic diagnostics produce a nonzero result.

## `vectis parse`

`vectis parse FILE` parses source and emits deterministic JSON representing the AST.

This command performs no runtime execution.

## `vectis plan`

`vectis plan FILE` parses and compiles source into the deterministic VECTIS execution graph.

The graph is emitted as JSON using the public execution-graph serialization contract.

## `vectis run`

`vectis run FILE` compiles the source and executes its validated execution graph through the deterministic runtime.

`vectis run --dry-run FILE` requests runtime dry-run behavior so node handlers are not invoked.

Runtime success is reflected in the process exit code and in the structured JSON result.

## Help and version

Running `vectis` without a command prints the main help.

Every command provides clear argparse-generated help, and `vectis --version` prints the installed VECTIS version.

## Exit behavior

The CLI uses explicit exit codes:

- `0` for successful toolchain operations;
- `1` for VECTIS syntax, semantic, compilation, or runtime failure;
- `2` for source-file or text-decoding failures.

## Architectural boundary

The CLI orchestrates existing parser, compiler, execution-graph, and runtime APIs. It does not redefine language semantics.

`check`, `parse`, and `plan` do not execute runtime handlers. `run` delegates execution to the deterministic VECTIS runtime.

Filesystem, process, and HTTP capabilities remain bounded by their explicit adapters and are not broadened by the CLI.
