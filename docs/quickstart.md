# VECTIS Quickstart

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Verify the installation:

```bash
vectis --version
vectis doctor
```

## Create a mission

Save this as `release-gate.vectis`:

```vectis
mission "Release gate" {
    source ready true;
    source score 92;

    let product upper("vectis");
    let approved ready && score >= 80;
    let message concat(product, " READY");

    assert score >= 70;

    when approved {
        publish message;
    } otherwise {
        publish "manual review";
    }
}
```

## Validate and inspect

```bash
vectis check release-gate.vectis
vectis tokens release-gate.vectis
vectis inspect release-gate.vectis
vectis plan release-gate.vectis
```

## Format

```bash
vectis fmt release-gate.vectis
vectis fmt --check release-gate.vectis
vectis fmt --write release-gate.vectis
```

## Execute

```bash
vectis run --dry-run release-gate.vectis
vectis run release-gate.vectis
```

Runtime JSON includes node states, failures, execution order, and resolved `node_values`.

## Explore the language

```bash
vectis builtins
vectis capabilities
```

## Launch VECTIS Studio

```bash
vectis studio
```

By default Studio listens only on `127.0.0.1:8765` and opens a browser. Use `--no-browser` when launching it on a headless system.
