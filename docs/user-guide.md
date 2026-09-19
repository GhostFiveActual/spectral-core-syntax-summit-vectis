<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS User Guide

## Purpose

VECTIS is a deterministic automation language. It converts source into typed syntax, validates the program, compiles an execution graph, and executes that graph through explicit runtime rules.

## Install

Create an isolated environment and install the package in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Confirm the installation with `vectis version` and `vectis doctor`.

## Create a project

```bash
vectis init ./project
cd ./project
```

Use `vectis new` as an alias for the same operation.

Validate every mission in the project:

```bash
vectis test .
```

## Declarations

A source declaration defines an initial value.

```vectis
source score 94;
source ready true;
source label "Spectral Core";
```

A let declaration defines a deterministic computed value.

```vectis
let approved ready && score >= 80;
let title upper(label);
```

An analyze declaration reserves an analysis node that an embedding runtime may connect to a handler.

```vectis
analyze findings;
```

## Expressions

VECTIS supports strings, numbers, booleans, references, function calls, parentheses, unary operators, and binary operators.

Operator precedence from lowest to highest is:

1. `||`
2. `&&`
3. `==` and `!=`
4. `>`, `>=`, `<`, and `<=`
5. `+` and `-`
6. `*`, `/`, and `%`
7. unary `!`, `+`, and `-`
8. primary values and function calls

## Built in functions

Use:

```bash
vectis builtins
```

to print the current registry.

The current function surface includes string normalization, string tests, replacement, bounded repetition, concatenation, length, numeric range checks, numeric clamping, minimum, maximum, rounding, conversion, and conditional selection.

Examples:

```vectis
let clean trim(raw_name);
let title upper(clean);
let bounded clamp(score, 0, 100);
let approved between(bounded, 80, 100);
let status if_else(approved, "AUTHORIZED", "REVIEW");
let message replace("GHOST FIVE READY", "READY", status);
```

## Assertions

Assertions enforce mission invariants.

```vectis
assert score >= 0 && score <= 100;
```

A false assertion fails its node and blocks later statements in the same block.

## Conditions

```vectis
when approved {
    publish "authorized";
} otherwise {
    publish "review";
}
```

Every node in each branch receives an explicit branch edge from the condition node.

## Capabilities

The standard capability names are filesystem, process, and http.

```vectis
require "filesystem";
request "http";
```

Granting a capability name does not perform an external action. The embedding application still needs an explicit handler or adapter.

## Diagnostics

VECTIS diagnostics are structured product data. Each diagnostic carries a stable code, severity, message, and source span. Lexer failures use the LEX family, syntax failures use SYN, semantic failures use SEM, and capability failures use CAP.

Use `vectis check` for focused validation or `vectis inspect` when the diagnostic should be reviewed beside tokens, syntax, and the compiled graph.

## Formatting

```bash
vectis fmt mission.vectis
vectis fmt --check mission.vectis
vectis fmt --write mission.vectis
```

## Inspection

```bash
vectis tokens mission.vectis
vectis parse mission.vectis
vectis plan mission.vectis
vectis inspect mission.vectis
vectis explain mission.vectis
```

Export graph formats:

```bash
vectis graph mission.vectis --format json
vectis graph mission.vectis --format dot
vectis graph mission.vectis --format mermaid
```

## Execution

```bash
vectis run --dry-run mission.vectis
vectis run mission.vectis
```

Runtime output includes success, execution order, node states, node values, and failures.

## Expression work

Evaluate one pure expression:

```bash
vectis eval 'if_else(93 >= 90, "READY", "REVIEW")'
```

Start an interactive session:

```bash
vectis repl
```

The REPL supports local scalar assignments for the current session.

## Examples

```bash
vectis examples
vectis examples release-gate
vectis examples functions
vectis examples readiness
```

## Applications

Launch the development workbench:

```bash
vectis studio
```

Launch the application demonstration:

```bash
vectis demo
```

Studio is for authoring and inspection. Mission Readiness demonstrates VECTIS embedded inside an application.

## Current language boundary

VECTIS 0.1 is an automation language, not a general purpose replacement for Python or another host language. The current value model is scalar. User defined functions, modules, structured collections, and bounded iteration remain future language work.
