<div align="center">

# VECTIS

### Ghost Five // Spectral Core

**A deterministic, capability-aware language and execution toolchain for auditable automation.**

[![CI](https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis/actions/workflows/ci.yml/badge.svg)](https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/release-v0.0.1-0f766e)](https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis/releases/tag/v0.0.1)
[![Python](https://img.shields.io/badge/python-3.14_verified-0f766e)](https://www.python.org/)

</div>

---

VECTIS is a domain-specific language for describing deterministic missions, validating them before execution, compiling them into an explicit execution graph, and running them through a capability-constrained runtime.

The project is developed by **Ghost Five // Spectral Core** with a simple design rule: automation should be inspectable before it executes and authority should be explicit rather than implied.

## Why VECTIS

VECTIS is built around a few deliberate properties:

- **Deterministic compilation** — the same valid source produces the same execution graph.
- **Semantic validation before execution** — invalid references and type errors are rejected before runtime work begins.
- **Explicit execution graphs** — dependencies and conditional branches are visible and serializable.
- **Capability-aware runtime boundaries** — external authority is declared and unavailable capability is denied.
- **Dry-run support** — inspect scheduling without invoking runtime handlers.
- **Structured diagnostics** — lexer, parser, semantic, and runtime failures preserve useful source context.
- **No dynamic `eval`/`exec` execution path** — runtime behavior stays inside explicit language and adapter boundaries.

## Quick start

```bash
git clone https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis.git
cd spectral-core-syntax-summit-vectis

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

Confirm the CLI:

```bash
vectis --version
vectis --help
```

## Your first VECTIS mission

```vectis
mission "Deploy when ready" {
    source deployment_ready true;
    source message "VECTIS is operational";

    when deployment_ready {
        publish message;
    } otherwise {
        request "manual-review";
    }
}
```

Save the source as `mission.vectis`, then inspect it progressively:

```bash
vectis check mission.vectis
vectis parse mission.vectis
vectis plan mission.vectis
vectis run --dry-run mission.vectis
vectis run mission.vectis
```

## CLI

| Command | Purpose |
| --- | --- |
| `vectis check FILE` | Validate syntax and semantics. |
| `vectis parse FILE` | Parse source and emit the AST as JSON. |
| `vectis plan FILE` | Compile source into the deterministic execution graph. |
| `vectis run --dry-run FILE` | Inspect deterministic scheduling without runtime side effects. |
| `vectis run FILE` | Execute the compiled graph through the VECTIS runtime. |
| `vectis --version` | Print the installed VECTIS version. |

## Execution model

```text
VECTIS source
     |
     v
   Lexer
     |
     v
   Parser
     |
     v
     AST
     |
     v
Semantic analysis
     |
     v
Execution graph
     |
     v
Deterministic runtime
     |
     v
Explicit capability adapters
```

The execution graph is the boundary between language meaning and runtime behavior. Dependencies, branch edges, and node values are explicit rather than hidden inside an opaque interpreter loop.

## Capability model

Capabilities are opt-in runtime authority. VECTIS does not treat the presence of a language statement as permission to perform an external action.

The current adapter layer includes controlled interfaces for:

- filesystem operations,
- process execution,
- HTTP requests.

Adapters enforce their own boundary rules such as filesystem root containment, process executable allowlists, no implicit parent-environment inheritance, structured process arguments, HTTP scheme restrictions, timeout limits, and explicit capability availability.

See [Architecture: Security](docs/architecture/security.md) for the detailed contract.

## Package and release validation

The v0.0.1 baseline has been validated through:

- the complete repository quality gate,
- 311 automated tests at the release baseline,
- a clean clone on a second Ghost Five system,
- editable package installation,
- independent VECTIS source authoring,
- source-reference conditional execution,
- isolated wheel and source-distribution builds,
- wheel installation into a fresh virtual environment,
- out-of-tree CLI execution from `/tmp`.

CI repeats the repository quality gate and package smoke path for future changes.

## Repository map

```text
src/vectis/             Core language, compiler, runtime, and adapters
examples/               Valid, invalid, and end-to-end VECTIS examples
docs/
  architecture/         Compiler, runtime, and security architecture
  design/               Design decisions and implementation contracts
  spec/                 Language specification and grammar
  playground/           Browser playground contract and assets
  release/              Release records and changelog material
  submission/           Original project/submission provenance
tests/                  Language, runtime, adapter, security, and UX tests
tools/                  Quality and engineering automation
competition/            Historical autonomous-build provenance
.github/                 CI, release automation, templates, and ownership
```

The product-facing implementation lives in `src/vectis/`. Historical competition and autonomous-build records are retained for provenance but are not required to understand the public VECTIS API.

## Documentation

Start with:

- [Quickstart](docs/quickstart.md)
- [User guide](docs/user-guide.md)
- [Documentation index](docs/README.md)
- [Architecture overview](docs/architecture/overview.md)
- [Compiler pipeline](docs/architecture/compiler-pipeline.md)
- [Runtime architecture](docs/architecture/runtime.md)
- [Security architecture](docs/architecture/security.md)
- [Grammar](docs/spec/grammar.md)
- [Release notes](docs/release/RELEASE.md)
- [Changelog](docs/release/CHANGELOG.md)

## Development

Run the authoritative repository gate:

```bash
bash tools/quality-gate.sh
```

Run the core Python suite directly:

```bash
python3 -m unittest discover -v
```

Build distributable artifacts:

```bash
python -m pip install build
python -m build
```

The GitHub CI workflow performs the quality gate, package build, isolated wheel install, and an out-of-tree VECTIS runtime smoke test.

## Security

VECTIS is designed around explicit capability boundaries and deterministic execution, but security issues should not be disclosed through a public issue before coordinated review.

See [SECURITY.md](SECURITY.md).

## Contributing

Contributions should preserve determinism, explicit authority boundaries, diagnostics, and the existing execution-graph contract.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Release

Current release: **v0.0.1**

Release artifacts are built as:

- `vectis_lang-0.0.1-py3-none-any.whl`
- `vectis_lang-0.0.1.tar.gz`

See the [GitHub Releases](https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis/releases) page for packaged artifacts.

## Ghost Five

**VECTIS** is a **Spectral Core** product within **Ghost Five**.

Spectral Core focuses on software engineering and systems that answer a practical question: **Can we build it?**

VECTIS applies that approach to deterministic automation: define the mission, validate the language, inspect the graph, constrain authority, then execute.

---

<div align="center">

**Ghost Five // Spectral Core // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
