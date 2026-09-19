<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS

VECTIS is the Spectral Core language and execution toolchain for deterministic automation. It gives a mission a defined syntax, validates it before runtime work, compiles it into an inspectable execution graph, and executes it through explicit authority boundaries.

The active development line is **0.1.0.dev0**. The **v0.0.1** tag remains the frozen engineering baseline.

## Language example

```vectis
mission "Release gate" {
    source ready true;
    source quality 94;
    source risk 22;

    let approved ready && quality >= 80 && risk <= 35;
    let status if_else(approved, "AUTHORIZED", "REVIEW");

    assert quality >= 0 && quality <= 100;
    assert risk >= 0 && risk <= 100;

    when approved {
        publish concat("VECTIS // ", status);
    } otherwise {
        publish "VECTIS // REVIEW";
    }
}
```

The same source can be formatted, validated, inspected, graphed, dry run, executed, and embedded inside an application.

## Install for development

```bash
git clone https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis.git
cd spectral-core-syntax-summit-vectis

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify the environment:

```bash
vectis version
vectis doctor
```

## Command surface

| Command | Purpose |
| --- | --- |
| `vectis check FILE` | Validate syntax and semantics. |
| `vectis tokens FILE` | Print the deterministic token stream. |
| `vectis parse FILE` | Print the typed syntax tree. |
| `vectis plan FILE` | Compile and print the execution graph. |
| `vectis inspect FILE` | Print tokens, syntax tree, diagnostics, and graph together. |
| `vectis run FILE` | Execute a validated mission. |
| `vectis run --dry-run FILE` | Inspect runtime scheduling without handlers. |
| `vectis run --capability NAME FILE` | Grant an explicit named runtime capability. |
| `vectis fmt FILE` | Print canonical formatting. |
| `vectis fmt --check FILE` | Verify canonical formatting. |
| `vectis fmt --write FILE` | Rewrite a source file canonically. |
| `vectis eval EXPRESSION` | Evaluate one pure VECTIS expression. |
| `vectis graph FILE --format json` | Export the execution graph as JSON. |
| `vectis graph FILE --format dot` | Export the execution graph as Graphviz DOT. |
| `vectis graph FILE --format mermaid` | Export the execution graph as Mermaid. |
| `vectis explain FILE` | Summarize the compiled mission structure. |
| `vectis init PATH` | Create a Ghost Five branded VECTIS project. |
| `vectis new PATH` | Alias for project creation. |
| `vectis test PATH` | Compile every VECTIS source file below a path. |
| `vectis examples` | List canonical examples. |
| `vectis examples NAME` | Print one canonical example. |
| `vectis repl` | Open the deterministic expression REPL. |
| `vectis builtins` | List deterministic built in functions. |
| `vectis capabilities` | List standard capability names. |
| `vectis doctor` | Report the local toolchain environment. |
| `vectis studio` | Launch the VECTIS Studio workbench. |
| `vectis app` | Alias for VECTIS Studio. |
| `vectis demo` | Launch the Mission Readiness application powered by VECTIS. |
| `vectis showcase` | Alias for the Mission Readiness demo. |
| `vectis version` | Print the installed VECTIS version. |

## Project workflow

Create a project:

```bash
vectis init ./my-vectis-project
cd ./my-vectis-project
vectis test .
```

Run the generated mission:

```bash
vectis run missions/main.vectis
```

Export the graph:

```bash
vectis graph missions/main.vectis --format mermaid
```

## VECTIS Studio

```bash
vectis studio
```

Studio is the language workbench. It exposes the source editor, formatter, diagnostics, execution graph, runtime states, resolved values, examples, and built in reference through the same compiler and runtime used by the CLI.

Studio binds to loopback by default.

## Mission Readiness demo

```bash
vectis demo
```

The Mission Readiness application demonstrates VECTIS as an embedded decision engine. The form generates real VECTIS source from structured inputs, compiles it, executes it, and displays the exact published result.

This is separate from Studio. Studio is the development workbench. Mission Readiness is a working application built on the VECTIS engine.

## Language capabilities

VECTIS currently supports scalar strings, numbers, booleans, references, computed values, deterministic function calls, arithmetic, comparison, boolean logic, assertions, conditional branches, publications, confidence, citations, capability requirements, capability requests, and explicit runtime handlers.

The built in function registry includes text normalization, comparison helpers, bounded repetition, numeric range helpers, conversions, conditional selection, and deterministic numeric operations.

Use:

```bash
vectis builtins
```

for the current machine readable registry.

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
Deterministic runtime
     ↓
Explicit adapters and handlers
```

The execution graph is the boundary between language meaning and runtime scheduling. External effects remain behind explicit capability adapters.

## Spectral Core standards

VECTIS is the reference implementation for Spectral Core engineering practice.

Start with:

1. [Spectral Core standards](docs/spectral-core/README.md)
2. [Engineering standard](docs/spectral-core/engineering-standard.md)
3. [Ghost Five writing standard](docs/spectral-core/writing-standard.md)
4. [Language standard](docs/spectral-core/language-standard.md)
5. [Release standard](docs/spectral-core/release-standard.md)
6. [VECTIS knowledge transfer](docs/spectral-core/knowledge-transfer.md)

## Repository quality

Run the complete gate:

```bash
bash tools/quality-gate.sh
```

The gate validates compilation, tests, imports, the public repository boundary, whitespace, secret patterns, symlink policy, Ghost Five branding, writing rules, and code purpose headers.

## Release status

| Version | Status |
| --- | --- |
| `v0.0.1` | Frozen engineering baseline. |
| `0.1.0.dev0` | Active development line. |
| `v0.1.0` | Public preview target after release gates are complete. |

A public open source release still requires an explicit license decision. No license is implied until one is deliberately added.
