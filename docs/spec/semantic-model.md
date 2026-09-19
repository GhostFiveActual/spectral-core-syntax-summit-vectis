<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Semantic Model

Status: normative for the 0.1 language line.

## Purpose

Semantic analysis runs after parsing and before execution graph generation. A program with semantic diagnostics does not produce a graph.

## Declarations

Source, let, and analyze introduce names into the declaration environment.

Duplicate declarations produce SEM002.

References must resolve to an earlier visible declaration. An unresolved reference produces SEM001.

## Scalar value types

The current semantic model tracks four coarse types:

1. string
2. number
3. boolean
4. unknown

Unknown represents a value that cannot be proven statically or may be supplied by a runtime handler.

## Built in functions

Function calls resolve against the deterministic registry in the evaluator.

An unknown function produces SEM003.

An invalid argument count produces SEM004.

The 0.1 registry includes text normalization, text tests, concatenation, replacement, bounded repetition, numeric helpers, numeric range checks, conversion, and conditional scalar selection.

Use the command below for the exact installed registry:

```bash
vectis builtins
```

## Type rules

Known contradictions are rejected before graph generation.

Examples include a nonboolean when condition, a nonboolean assert condition, and a nonnumeric confidence expression.

These failures use SEM005.

## Graph eligibility

Compilation occurs only when semantic diagnostics are empty.

References become dependency edges.

Conditional bodies become explicit true or false branch edges.

Assertions become dependency guards for statements that follow them in the same block.

## Runtime values

The runtime resolves serialized expressions against values produced by dependency nodes. Pure function calls, arithmetic, comparisons, and boolean operations can therefore use actual runtime values while preserving deterministic topological scheduling.

## Current boundary

The 0.1 value model is scalar. User defined functions, modules, general structured collections, and bounded iteration remain future language work.
