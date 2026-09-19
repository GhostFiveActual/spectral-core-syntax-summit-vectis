<div align="center">

# VECTIS

### Ghost Five // Spectral Core

**Deterministic automation you can inspect before it runs.**

`source → parse → validate → plan → authorize → execute`

</div>

---

VECTIS is a deterministic, capability-aware domain-specific language and execution toolchain for building auditable automation. A VECTIS mission is parsed into a typed AST, semantically validated, compiled into an explicit execution graph, and executed through a runtime that keeps external authority behind named capability boundaries.

The current development line is **0.1.0.dev0**, targeting the first public-preview release. The existing **v0.0.1** tag remains the frozen engineering baseline.

## What VECTIS looks like

```vectis
mission "Release gate" {
    source ready true;
    source quality_score 0.96;

    let product upper("vectis");
    let approved ready && quality_score >= 0.90;
    let message concat(product, " READY");

    assert quality_score >= 0.80;

    when approved {
        publish message;
    } otherwise {
        request "manual-review";
    }
}
```

VECTIS can validate that source, show the tokens and AST, compile an execution graph, dry-run the schedule, execute it, and expose the resolved value of each runtime node.

## Why VECTIS

- **Deterministic planning** — valid source lowers to an explicit, serializable execution graph.
- **Pre-execution validation** — syntax, references, function calls, arity, and selected type rules are checked before a graph is produced.
- **Runtime expression evaluation** — references, arithmetic, comparisons, boolean logic, and pure built-in functions resolve from actual node values.
- **Explicit branch gating** — every node in a `when` or `otherwise` branch is gated by the condition node.
- **Assertions** — `assert` can stop and block subsequent work when an invariant fails.
- **Capability boundaries** — filesystem, process, and HTTP authority remain opt-in instead of implicit.
- **No dynamic Python execution** — VECTIS does not use Python `eval`, `exec`, or implicit shell execution for language evaluation.
- **Local-first Studio** — VECTIS ships with a browser-based application served directly by the installed package, with no CDN dependency.

## Install for development

```bash
git clone https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis.git
cd spectral-core-syntax-summit-vectis

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Then:

```bash
vectis --version
vectis doctor
```

## CLI

| Command | Purpose |
| --- | --- |
| `vectis check FILE` | Validate syntax and semantics. |
| `vectis tokens FILE` | Emit the deterministic lexer token stream. |
| `vectis parse FILE` | Emit the typed AST as JSON. |
| `vectis plan FILE` | Compile and emit the execution graph. |
| `vectis inspect FILE` | Emit tokens, AST, diagnostics, and graph in one document. |
| `vectis run FILE` | Execute a compiled mission. |
| `vectis run --dry-run FILE` | Show deterministic runtime scheduling without handlers. |
| `vectis run --capability NAME FILE` | Grant an explicit named runtime capability. |
| `vectis fmt FILE` | Print canonical VECTIS formatting. |
| `vectis fmt --check FILE` | Verify canonical formatting. |
| `vectis fmt --write FILE` | Rewrite a file canonically. |
| `vectis builtins` | List deterministic built-in functions. |
| `vectis capabilities` | List standard capability names. |
| `vectis doctor` | Inspect the local VECTIS/Python environment. |
| `vectis studio` | Launch VECTIS Studio. |
| `vectis app` | Alias for VECTIS Studio. |

## Built-in functions

The 0.1 language line introduces deterministic pure function calls:

```text
upper(text)          lower(text)          trim(text)
length(text)         concat(value, ...)   contains(text, part)
starts_with(a, b)    ends_with(a, b)      abs(number)
round(number, n?)    min(number, ...)     max(number, ...)
string(value)        number(value)        boolean(value)
```

Built-ins do not receive filesystem, process, or network authority. Their only inputs are evaluated VECTIS scalar values.

## Operators

```text
||
&&
==  !=
>  >=  <  <=
+  -
*  /  %
!  unary +  unary -
```

`+` supports numeric addition and string-to-string concatenation. Other arithmetic operators require numbers.

## VECTIS Studio

Launch:

```bash
vectis studio
```

Studio opens on loopback by default and provides:

- Ghost Five / Spectral Core product UI,
- mission source editor with line numbers and keyboard shortcuts,
- Check / Plan / Run / Format actions,
- execution graph visualization,
- runtime states and resolved node values,
- AST and raw plan inspection,
- diagnostics,
- example missions,
- built-in function reference.

Studio refuses non-loopback binding unless `--allow-remote` is explicitly supplied.

## Execution model

```text
VECTIS source
     ↓
Lexer
     ↓
Parser
     ↓
Typed AST
     ↓
Semantic analysis
     ↓
Execution graph
     ↓
Deterministic expression/runtime engine
     ↓
Explicit capability adapters
```

The execution graph is the stable boundary between language meaning and runtime scheduling. Runtime handlers and capability adapters are explicit extension points rather than hidden behavior.

## Repository structure

```text
src/vectis/             Language, compiler, evaluator, runtime, adapters, Studio
src/vectis/studio_assets/
                        Packaged local-first Studio UI
examples/               Canonical valid/invalid/demo programs
docs/
  architecture/         System architecture and trust boundaries
  design/               Component design contracts
  qa/                   Conformance/security records
  release/              Release notes, history, public-release checklist
  spec/                 Normative language specification
  ux/                   UX and diagnostics guidance
tests/                  Product, language, runtime, security, Studio tests
tools/                  Product quality and conformance tooling
.github/                 CI, release automation, ownership and templates
```

Internal autonomous build-state, competition task contracts, controller code, and original submission material are intentionally **not part of the public product tree**.

## Development quality gate

```bash
bash tools/quality-gate.sh
```

The gate compiles the package, runs the full test suite, imports every VECTIS module, verifies the public-repository boundary, checks whitespace, scans common secret patterns, and checks the repository symlink boundary.

## Packaging

```bash
python -m pip install build
python -m build
```

The package includes the VECTIS Studio HTML/CSS/JavaScript assets so `vectis studio` works from an installed wheel rather than requiring a source checkout.

## Security model

VECTIS intentionally separates language evaluation from privileged adapters. Standard capability names currently include:

- `filesystem`
- `process`
- `http`

See [Security architecture](docs/architecture/security.md) and [Security policy](SECURITY.md).

## Documentation

Start with:

- [Quickstart](docs/quickstart.md)
- [User guide](docs/user-guide.md)
- [Language grammar](docs/spec/grammar.md)
- [Lexical specification](docs/spec/lexical-spec.md)
- [Semantic model](docs/spec/semantic-model.md)
- [Architecture overview](docs/architecture/overview.md)
- [VECTIS Studio](docs/studio.md)
- [Public release checklist](docs/release/PUBLIC_RELEASE_CHECKLIST.md)
- [Roadmap](ROADMAP.md)

## Release status

- `v0.0.1` — frozen engineering baseline.
- `0.1.0.dev0` — current development snapshot for the first public preview.
- `v0.1.0` — intended first public-preview release after release-gate completion.

A public/open-source release still requires an explicit **license decision**. No license is implied by this repository until one is deliberately added.

---

<div align="center">

**Ghost Five // Spectral Core // VECTIS**

**Define the mission. Inspect the graph. Constrain authority. Execute.**

</div>
