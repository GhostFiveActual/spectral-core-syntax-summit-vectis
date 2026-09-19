# VECTIS Changelog

## 0.1.0.dev0 — in development

### Repository

- Removed autonomous competition/controller/submission build artifacts from the public product tree.
- Moved historical v0.0.1 release notes under `docs/release/history/`.
- Reworked the quality gate around the public product boundary.

### Language

- Added `let` deterministic value declarations.
- Added pure built-in function-call expressions.
- Added `>`, `<`, and `%` operators.
- Added `assert` mission guards.
- Added semantic diagnostic codes `SEM001`–`SEM005`.
- Added runtime evaluation of expressions using actual dependency values.
- Added resolved node values to runtime results.
- Gated every node in conditional branches explicitly.

### CLI

Added:

- `tokens`
- `inspect`
- `fmt`
- `builtins`
- `capabilities`
- `doctor`
- `studio`
- `app`

`run` now also accepts repeatable `--capability NAME` grants.

### Application

- Added packaged VECTIS Studio.
- Added local API for check/parse/plan/run/format.
- Added execution graph visualization, runtime inspector, diagnostics, AST/plan views, examples, formatter, and built-in reference.

## 0.0.1 — engineering baseline

- Initial deterministic lexer/parser/AST/semantic/compiler/runtime pipeline.
- Explicit execution graph and branch edges.
- Filesystem, process, and HTTP capability adapters.
- Source-reference condition runtime fix.
- Packaged CLI with check/parse/plan/run.
- Frozen engineering release tag and artifacts.
