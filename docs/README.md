<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Documentation

## Start here

| Document | Purpose |
| --- | --- |
| [Quickstart](quickstart.md) | Install, create a project, validate, inspect, execute, and launch applications. |
| [User guide](user-guide.md) | Complete current language and CLI workflow. |
| [Demo](demo.md) | Scripted demo and Mission Readiness application. |
| [VECTIS Studio](studio.md) | Local development workbench. |
| [Roadmap](../ROADMAP.md) | Planned language and product work. |

## Spectral Core standards

The Spectral Core standard set lives under [docs/spectral-core](spectral-core/README.md). These documents capture the engineering, writing, language, release, and knowledge transfer rules that VECTIS established for the team.

## Language specification

| Document | Purpose |
| --- | --- |
| [Grammar](spec/grammar.md) | Normative concrete syntax. |
| [Lexical specification](spec/lexical-spec.md) | Tokens, identifiers, operators, comments, strings, and numbers. |
| [Semantic model](spec/semantic-model.md) | Declarations, references, functions, type rules, and graph eligibility. |

## Architecture

The architecture directory documents the compiler pipeline, runtime, security boundary, and threat model.

## Engineering design

The design directory contains component contracts for the syntax tree, parser, semantic analyzer, execution graph, runtime, diagnostics, CLI, capabilities, and adapters.

## Quality

The qa directory documents language conformance and security review. The executable source of truth is the test suite plus `tools/quality-gate.sh`.

## Releases

The release directory contains current release records, historical release notes, and the public release checklist.
