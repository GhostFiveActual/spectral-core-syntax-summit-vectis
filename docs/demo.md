<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Demonstration Paths

VECTIS provides two different demonstrations because they prove different parts of the product.

## Scripted compiler and runtime demo

Run:

```bash
python examples/demo/run_demo.py
```

This validates the canonical example through the public parser, compiler, graph, and runtime APIs.

The same source can be inspected through the CLI:

```bash
vectis inspect examples/demo/demo.vectis
vectis run examples/demo/demo.vectis
```

## Mission Readiness application

Run:

```bash
vectis demo
```

The application accepts structured mission inputs and sends them to a local VECTIS backed API. The backend generates VECTIS source, compiles it, executes it, and returns the actual graph and runtime result.

The application demonstrates that VECTIS can sit inside another product rather than requiring a user to work directly in the language.

## Studio

Run:

```bash
vectis studio
```

Studio is the development workbench for editing and inspecting VECTIS. It is not the same product surface as Mission Readiness.
