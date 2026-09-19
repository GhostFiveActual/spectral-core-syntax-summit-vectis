# VECTIS User Guide

## Install

For local development, create an isolated environment and install the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

A packaged release can be installed from its wheel with `python -m pip install <wheel>`.

VECTIS is a deterministic language for expressing inspectable automation missions. Source is validated and compiled into an execution graph before the runtime schedules nodes.

## 1. Mission structure

```vectis
mission "Example" {
    source input 42;
    let doubled input * 2;
    publish doubled;
}
```

A file may contain multiple statements, including mission blocks. Mission names are strings.

## 2. Declarations

### `source`

Declares an input or initial value:

```vectis
source score 93;
source enabled true;
source label "Ghost Five";
```

### `let`

Declares a deterministic computed value:

```vectis
let passing score >= 80;
let title concat(upper(label), " // VECTIS");
```

References create explicit execution-graph dependency edges.

### `analyze`

Preserves the analysis-node contract for workflows that attach an explicit runtime handler:

```vectis
analyze findings;
analyze score raw_score;
```

## 3. Expressions

VECTIS supports strings, numbers, booleans, references, function calls, parentheses, unary operators, and binary operators.

```vectis
let result (base + bonus) * 2;
let approved enabled && score >= 80;
let label upper(trim(raw_label));
```

Operator precedence, lowest to highest:

1. `||`
2. `&&`
3. `==`, `!=`
4. `>`, `>=`, `<`, `<=`
5. `+`, `-`
6. `*`, `/`, `%`
7. unary `!`, `+`, `-`
8. primary values and function calls

## 4. Built-in functions

Use `vectis builtins` for the machine-readable registry.

String/value functions:

- `upper(text)`
- `lower(text)`
- `trim(text)`
- `length(text)`
- `concat(value, ...)`
- `contains(text, part)`
- `starts_with(text, prefix)`
- `ends_with(text, suffix)`

Numeric functions:

- `abs(number)`
- `round(number)`
- `round(number, digits)`
- `min(number, ...)`
- `max(number, ...)`

Conversions:

- `string(value)`
- `number(value)`
- `boolean(value)`

Built-ins are pure and deterministic. They do not acquire capabilities.

## 5. Conditions

```vectis
when ready && score >= 90 {
    publish "ship";
} otherwise {
    publish "review";
}
```

Every node in each branch receives an explicit branch edge from the condition node. The inactive branch is skipped deterministically.

## 6. Assertions

Use `assert` for mission invariants:

```vectis
assert score >= 70;
publish "score accepted";
```

A false assertion fails its node. Subsequent nodes in the same block are dependency-gated by that assertion and become blocked.

## 7. Outputs and metadata statements

```vectis
publish result;
confidence 0.94;
citations [primary_source, secondary_source];
```

`confidence` must evaluate to a number.

## 8. Capabilities

```vectis
require "filesystem";
request "http";
```

Capabilities are explicit runtime authority. The standard names are `filesystem`, `process`, and `http`.

The CLI can grant a named capability for validation/runtime gating:

```bash
vectis run --capability filesystem mission.vectis
```

Granting a capability name does not itself perform I/O. Actual external effects require an explicit runtime handler/adapter integration.

## 9. Diagnostics

Diagnostics include a stable code, severity, message, and source span. Current code families include:

- `LEXxxx` — lexical errors
- `SYNxxx` — syntax errors
- `SEMxxx` — semantic errors

Examples include unresolved references, duplicate declarations, unknown built-in functions, invalid function arity, and selected type mismatches.

## 10. CLI workflow

A useful development loop is:

```bash
vectis fmt --check mission.vectis
vectis check mission.vectis
vectis inspect mission.vectis
vectis run --dry-run mission.vectis
vectis run mission.vectis
```

## 11. VECTIS Studio

Launch with:

```bash
vectis studio
```

Studio exposes the source editor, diagnostics, execution graph, raw plan, AST, runtime states, runtime values, examples, formatter, and built-in reference through a local-first UI.

## 12. Current scope

The 0.1 language line deliberately does **not** yet include:

- user-defined function declarations,
- modules/imports,
- loops,
- asynchronous tasks,
- general collection/list values outside the existing `citations [...]` statement,
- implicit adapter execution from language syntax.

Those are expansion areas for later releases and should be added without weakening deterministic planning or capability boundaries.
