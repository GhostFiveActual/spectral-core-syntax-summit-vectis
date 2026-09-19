<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Studio

VECTIS Studio is the local language workbench packaged with the VECTIS Python distribution.

## Launch

```bash
vectis studio
```

The `vectis app` command is an alias.

## Workspace

Studio provides:

1. Mission source editing.
2. Line and cursor tracking.
3. Canonical examples.
4. Formatting.
5. Check, plan, and run actions.
6. Execution metrics.
7. Native execution graph visualization.
8. Runtime state and value inspection.
9. Diagnostics.
10. Raw plan and syntax tree views.
11. Built in function reference.

## Local API

Studio uses local JSON endpoints for health, examples, built ins, check, parse, plan, run, and format.

The server binds to loopback by default. Remote binding requires explicit opt in.

## Product boundary

Studio is the development workbench. The Mission Readiness demo launched by `vectis demo` is a separate application that embeds VECTIS as its decision engine.

Both products use the same canonical compiler and runtime modules.
