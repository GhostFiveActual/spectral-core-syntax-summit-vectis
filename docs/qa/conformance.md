# VECTIS Language Conformance Suite

The VECTIS conformance suite provides deterministic checks for the
language's lexical, syntax, semantic, invalid-input, and regression
behavior.

`tools/conformance.py` contains canonical fixtures and a standalone
runner. `tests/test_conformance.py` verifies the same behavior through
the repository test suite.

## Lexical conformance

Positive lexical fixtures are tokenized with the canonical VECTIS
lexer. Lexical conformance does not treat arbitrary expressions as
standalone programs.

## Syntax conformance

Positive syntax fixtures use canonical VECTIS statements and mission
blocks. Negative fixtures intentionally contain invalid VECTIS and must
raise a lexer or parser error.

## Semantic conformance

Semantic-valid fixtures parse and compile without diagnostics and
produce an execution graph. Semantic-invalid fixtures remain
syntactically valid but must produce deterministic semantic diagnostics
and no execution graph.

## Regression conformance

Regression fixtures are compiled repeatedly and their execution-graph
serialization must remain deterministic.

## Running the suite

Run the standalone matrix with:

    python3 tools/conformance.py

Run the unit tests with:

    python3 -m unittest -v tests.test_conformance

The suite is local, deterministic, and does not require network access.

## Contract vocabulary

`compiler`, `runtime`
