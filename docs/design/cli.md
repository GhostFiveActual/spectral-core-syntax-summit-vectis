<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Command Line Toolchain

## Purpose

The VECTIS command line is the primary operational interface for the language, compiler, runtime, project workflow, graph inspection, and local applications.

It is designed for direct use by a developer and for predictable use from scripts and CI.

## Commands

| Command | Contract |
| --- | --- |
| `check` | Parse, analyze, and compile without execution. |
| `tokens` | Emit lexer tokens as JSON. |
| `parse` | Emit the typed syntax tree as JSON. |
| `plan` | Emit the execution graph as JSON. |
| `inspect` | Emit tokens, syntax tree, diagnostics, and graph together. |
| `run` | Execute the validated graph. |
| `fmt` | Print, verify, or write canonical formatting. |
| `eval` | Evaluate one pure scalar expression. |
| `graph` | Export JSON, Graphviz DOT, or Mermaid graph text. |
| `explain` | Emit a structural mission summary. |
| `init` | Create a branded project scaffold. |
| `new` | Alias for `init`. |
| `test` | Compile every VECTIS file under a path. |
| `examples` | List or print canonical examples. |
| `repl` | Run an interactive deterministic expression session. |
| `builtins` | Emit the built in function registry. |
| `capabilities` | Emit the standard capability registry. |
| `doctor` | Report local runtime information. |
| `version` | Print the installed version. |
| `studio` | Launch VECTIS Studio. |
| `app` | Alias for Studio. |
| `demo` | Launch the Mission Readiness application. |
| `showcase` | Alias for the demo application. |

## Input behavior

Commands that accept source use a file path or standard input. Omitting the file for a source command reads from standard input.

## Exit behavior

| Code | Meaning |
| --- | --- |
| `0` | Requested operation completed successfully. |
| `1` | VECTIS validation, compilation, project test, or runtime execution failed. |
| `2` | User input, path, encoding, or command data was invalid. |

## Boundary

The CLI routes requests into the public lexer, parser, semantic analyzer, compiler, runtime, formatter, product helpers, Studio, and demo application. It does not define a second copy of the language semantics.
