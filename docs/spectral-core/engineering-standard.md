<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# Spectral Core Engineering Standard

## Repository discipline

Every repository must present one product surface. Internal build state, autonomous controller state, competition material, temporary artifacts, generated caches, and local environment files do not belong in the public product tree.

Source code, tests, documentation, examples, release records, and automation should each have a clear location and purpose.

## Code comments

Code should explain intent where the implementation alone is not enough. Comments are not a transcript of the code.

Every source, test, tool, configuration, and example file should identify Ghost Five and Spectral Core near the beginning of the file and include a short statement of purpose.

Functions and classes should use names that carry most of the meaning. Comments should explain contracts, security boundaries, nonobvious decisions, and failure behavior.

## Implementation rules

1. Prefer deterministic behavior when the problem permits it.
2. Keep external authority explicit.
3. Validate input before side effects.
4. Make security boundaries fail closed.
5. Keep public APIs small and intentional.
6. Document compatibility behavior instead of hiding it.
7. Add tests with new behavior before merge.
8. Keep generated artifacts separate from source of truth.
9. Require architecture review before introducing dynamic execution.
10. Give user facing commands useful exit codes and readable diagnostics.

## Testing

A change is not complete because one local happy path worked. Tests should cover the contract, expected failures, boundary conditions, and security behavior.

CI should test every supported runtime version declared by the package.

## Quality gate

Every Spectral Core repository should provide one command that validates the complete release surface. VECTIS uses tools/quality-gate.sh.

The gate should be safe to run repeatedly and should fail on policy violations instead of silently correcting them.
