# Official VECTIS Examples

The `examples` tree provides executable reference material for the
canonical VECTIS grammar, compiler, semantic analyzer, and deterministic
execution-graph pipeline.

## Valid examples

Files in `examples/valid/` are expected to pass lexical analysis,
parsing, semantic analysis, and compilation.

### `end-to-end.vectis`

The end-to-end example demonstrates a complete deterministic workflow:
a mission, source declarations, a conditional branch, publishing, and a
human-review fallback.

It is intended to exercise the normal path from VECTIS source through
the parser, semantic analyzer, compiler, and execution graph.

### `capability-workflow.vectis`

The capability workflow demonstrates explicit capability declarations
using `require` and `request`.

Capabilities remain declarative in VECTIS source. Runtime authority is
resolved through the capability model and explicit adapters rather than
being implicitly granted by an example program.

## Syntax-invalid examples

Files under `examples/invalid/` intentionally violate the canonical
grammar. They are expected to fail parsing with source-location
diagnostics.

These examples document malformed syntax and are not valid programs.

## Semantic-invalid examples

Files under `examples/semantic-invalid/` are syntactically valid VECTIS
programs that intentionally fail semantic validation.

`unresolved-reference.vectis` demonstrates use of a reference that has
not been declared.

`type-mismatch.vectis` demonstrates a semantic type violation selected
from behavior enforced by the current semantic analyzer.

Semantic-invalid examples must parse successfully but must not produce
a valid compiled execution graph.

## Tests

`tests/test_examples.py` verifies that:

- official valid examples parse and compile;
- compilation of the end-to-end example is deterministic;
- capability workflow syntax remains valid;
- syntax-invalid examples fail parsing;
- semantic-invalid examples parse but produce semantic diagnostics; and
- semantic-invalid programs do not compile into execution graphs.

The examples are part of the language contract and should remain
consistent with the canonical grammar and current deterministic
compiler behavior.
