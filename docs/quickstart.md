<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Quickstart

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Verify the installation:

```bash
vectis version
vectis doctor
```

## Create a project

```bash
vectis init ./vectis-project
cd ./vectis-project
```

The scaffold contains a branded README, project metadata, and a missions directory with an executable starter mission.

## Validate the project

```bash
vectis test .
```

## Inspect the mission

```bash
vectis check missions/main.vectis
vectis inspect missions/main.vectis
vectis graph missions/main.vectis --format mermaid
```

## Execute the mission

```bash
vectis run --dry-run missions/main.vectis
vectis run missions/main.vectis
```

## Evaluate an expression

```bash
vectis eval 'clamp(108, 0, 100)'
vectis eval 'if_else(94 >= 80, "AUTHORIZED", "REVIEW")'
```

## Explore the language

```bash
vectis builtins
vectis capabilities
vectis examples
vectis examples readiness
vectis repl
```

## Launch Studio

```bash
vectis studio
```

Studio is the language workbench.

## Launch the demo application

```bash
vectis demo
```

Mission Readiness is a working application that uses VECTIS as its decision engine.
