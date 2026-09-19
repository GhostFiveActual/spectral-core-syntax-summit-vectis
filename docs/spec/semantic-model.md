# VECTIS Semantic Model — 0.1

## Purpose

Semantic analysis runs after parsing and before graph generation. A program with semantic diagnostics does not produce an execution graph.

## Declarations

`source`, `let`, and `analyze` introduce names into the declaration environment. Duplicate names are rejected with `SEM002`.

References must resolve to an earlier visible declaration. Unresolved references produce `SEM001`.

## Value types

The semantic analyzer tracks four coarse types:

- `string`
- `number`
- `boolean`
- `unknown`

`unknown` is used when a value may be supplied by a runtime handler or cannot be statically inferred.

## Built-in functions

Function calls resolve against the deterministic built-in registry.

- Unknown function: `SEM003`
- Invalid argument count: `SEM004`

Return types for standard built-ins are known to the analyzer and feed later expression checks.

## Selected type rules

- `when` conditions must be boolean or `unknown`.
- `assert` conditions must be boolean or `unknown`.
- `confidence` must be numeric or `unknown`.

Other expression operand checks are also enforced by the deterministic evaluator when values are resolved.

## Graph eligibility

Compilation occurs only when semantic diagnostics are empty. References become dependency edges. Branch bodies become explicit true/false branch edges. Assertions become dependency guards for statements that follow them in the same block.

## Runtime expression semantics

The runtime resolves each node's serialized canonical expression against values already produced by dependency nodes. This supports dynamic reference evaluation rather than relying only on compile-time literal folding.

Pure function calls, arithmetic, comparisons, and boolean operations therefore work with actual runtime node values while preserving deterministic topological scheduling.
