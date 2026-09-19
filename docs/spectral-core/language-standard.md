<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# Spectral Core Language Standard

## Purpose

VECTIS established the language design baseline for Spectral Core. Future domain specific languages should reuse these rules unless a documented requirement justifies a different approach.

## Core rules

1. Parse source into typed structures before execution.
2. Preserve source locations through diagnostics.
3. Perform semantic validation before runtime work.
4. Lower valid source into an inspectable intermediate representation.
5. Keep runtime scheduling deterministic.
6. Keep external effects behind explicit adapters or capabilities.
7. Avoid host language dynamic execution and implicit shell execution.
8. Make formatting deterministic.
9. Keep diagnostics stable enough for tools and users.
10. Treat examples as executable contracts and test them.

## Syntax direction

Syntax should be small enough to understand from one specification. New syntax must have a concrete grammar, parser coverage, semantic behavior, formatter behavior, runtime behavior when applicable, examples, and tests.

## Runtime direction

The runtime owns scheduling and value resolution. Adapters own external effects. The language does not acquire authority merely because source text names an operation.

## Tooling direction

A usable Spectral Core language should provide validation, formatting, inspection, execution, environment diagnostics, project initialization, testing, and a demonstration surface from one command line entry point.
