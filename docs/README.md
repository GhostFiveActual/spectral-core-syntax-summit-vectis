# VECTIS Documentation

The documentation tree is organized around the public VECTIS product.

## Start here

- [Quickstart](quickstart.md) — install, validate, plan, run, and launch Studio.
- [User guide](user-guide.md) — language workflow, values, functions, assertions, branches, capabilities, and CLI.
- [Demo](demo.md) — canonical demonstration path.
- [VECTIS Studio](studio.md) — local-first application architecture and operation.
- [Product roadmap](../ROADMAP.md) — planned language, adapter, and Studio evolution.

## Language specification

- [Grammar](spec/grammar.md) — normative concrete grammar.
- [Lexical specification](spec/lexical-spec.md) — tokens, identifiers, operators, comments, strings, and numbers.
- [Semantic model](spec/semantic-model.md) — declarations, references, built-ins, type rules, and graph eligibility.

## Architecture

- [Overview](architecture/overview.md)
- [Compiler pipeline](architecture/compiler-pipeline.md)
- [Runtime](architecture/runtime.md)
- [Security](architecture/security.md)
- [Threat model](architecture/threat-model.md)

## Engineering design

`design/` contains deeper component contracts for the AST, parser, semantic analyzer, IR, runtime, diagnostics, CLI, capability model, and adapters.

## Quality

`qa/` documents language conformance and security review. The executable source of truth is the automated test suite plus `tools/quality-gate.sh`.

## Releases

- [Current development release record](release/RELEASE.md)
- [Changelog](release/CHANGELOG.md)
- [Public-release checklist](release/PUBLIC_RELEASE_CHECKLIST.md)
- [v0.0.1 engineering-baseline notes](release/history/v0.0.1.md)

Internal autonomous-build records and original competition/submission artifacts are intentionally kept outside the public product repository.
