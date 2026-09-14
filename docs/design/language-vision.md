# Language Vision

Modern automation often forces users to coordinate several unrelated systems:

- YAML
- JSON
- shell scripting
- CI/CD configuration
- APIs
- schedulers
- workflow engines
- agent frameworks

VECTIS provides a constrained domain-specific language that expresses the
workflow rather than the implementation glue.

## Design Principles

Readable, not ambiguous.

Declarative where possible.

Explicit where consequences matter.

Deterministic.

Composable.

Safe by default.

Accessible without requiring expertise in every underlying platform.

## AI Boundary

AI may suggest VECTIS source.

Once source exists, its meaning is determined by formal syntax and semantics.
