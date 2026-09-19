<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Examples

The canonical examples live under `examples/` and are covered by automated tests.

For the 0.1 language surface, start with:

```text
examples/valid/release-gate.vectis
examples/valid/functions.vectis
examples/valid/assertions.vectis
```

Use:

```bash
vectis inspect examples/valid/release-gate.vectis
vectis run examples/valid/release-gate.vectis
```

The invalid and semantic-invalid directories provide deterministic negative fixtures for diagnostics and conformance testing.
