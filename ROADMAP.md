# VECTIS Roadmap

VECTIS evolves by expanding expressiveness without weakening deterministic planning, inspectability, or explicit authority boundaries.

## 0.1 — Public preview

Implemented in the current `0.1.0.dev0` development line:

- `let` computed declarations,
- `assert` mission guards,
- pure deterministic built-in functions,
- comparison/modulo operators,
- runtime evaluation of general scalar expressions,
- resolved node values in runtime results,
- expanded CLI (`tokens`, `inspect`, `fmt`, `builtins`, `capabilities`, `doctor`, `studio`/`app`),
- VECTIS Studio local-first visual application,
- cleaned public product repository and release automation.

Release gates still outstanding include the explicit license decision and CI proof across Python 3.11–3.14.

## 0.2 — Reusable language units

Planned design work:

- user-defined pure functions,
- explicit modules/imports,
- namespaced function discovery,
- function signatures and return-type checking,
- deterministic module graph / cycle detection.

User-defined functions should remain pure by default. External authority should continue to cross explicit capability/adapter boundaries rather than becoming ordinary function behavior.

## 0.3 — Structured data

Planned design work:

- list values,
- map/object values,
- indexing/member access,
- deterministic collection built-ins such as `map`, `filter`, `any`, and `all`,
- bounded iteration constructs designed so planning remains inspectable.

## 0.4 — First-class actions and adapters

Planned design work:

- explicit action invocation syntax,
- typed adapter inputs/outputs,
- capability declarations associated with action signatures,
- stronger dry-run action plans,
- structured action result values.

No action syntax should provide implicit shell/network/filesystem authority.

## Studio direction

VECTIS Studio should grow into the primary visual workbench:

- graph-node selection and dependency inspection,
- source-span ↔ graph-node synchronization,
- diagnostics inline in the editor,
- mission templates,
- capability configuration UI,
- execution timeline/history,
- diff view for formatted/planned changes,
- reusable module/function browser,
- optional packaged desktop shell after the browser-local product stabilizes.

## Compatibility policy

`v0.0.1` remains immutable as the engineering baseline. Development proceeds through new commits/releases; published tags are never rewritten.
