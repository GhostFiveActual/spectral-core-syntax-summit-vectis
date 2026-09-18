# VECTIS Submission Demo

The submission demo is a compact end-to-end example of the VECTIS language
toolchain. The canonical source is `examples/demo/demo.vectis`, and
`examples/demo/run_demo.py` provides a deterministic compiler-facing runner.

## Demo source

The demo declares two source values and uses a `when` / `otherwise` branch.
The language remains deterministic: the lexer tokenizes the source, the parser
constructs the AST, semantic analysis validates references, and the compiler
lowers the valid program into an execution graph.

## Run the compiler demo

From the repository root:

```text
PYTHONPATH=src python3 examples/demo/run_demo.py
```

The runner parses and compiles the source and prints the execution graph as
JSON. If a diagnostic is produced, or compilation does not produce a graph,
the runner exits with an error rather than hiding the failure.

## CLI workflow

The same demo can be exercised through the VECTIS command-line workflow:

```text
vectis check examples/demo/demo.vectis
vectis parse examples/demo/demo.vectis
vectis plan examples/demo/demo.vectis
vectis run --dry-run examples/demo/demo.vectis
```

The final command exercises the runtime in dry-run mode so the execution plan
can be inspected without performing external effects.

## Deterministic submission behavior

The submission artifacts use canonical VECTIS syntax only. The `.vectis` file
contains no Markdown fences, YAML metadata, JSON wrapper, or historical syntax.
Tests verify that the demo lexes, parses, compiles without diagnostics, produces
an execution graph, and remains deterministic across repeated compilation.
