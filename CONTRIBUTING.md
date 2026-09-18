# Contributing to VECTIS

VECTIS favors deterministic behavior, explicit contracts, small reviewable changes, and tests that exercise the real compiler/runtime path.

## Development setup

```bash
git clone https://github.com/GhostFiveActual/spectral-core-syntax-summit-vectis.git
cd spectral-core-syntax-summit-vectis

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

## Before changing code

Read the relevant contract:

- `docs/spec/grammar.md`
- `docs/architecture/compiler-pipeline.md`
- `docs/architecture/runtime.md`
- `docs/architecture/security.md`

Do not silently broaden syntax, runtime authority, or adapter access.

## Required checks

```bash
bash tools/quality-gate.sh
```

For runtime/compiler changes, add at least one test that exercises the actual source-to-runtime path rather than only constructing IR nodes manually.

For package-affecting changes:

```bash
python -m pip install build
python -m build
```

Then install the generated wheel into a fresh virtual environment and execute VECTIS from outside the repository directory.

## Pull requests

A focused pull request should explain:

1. what behavior changes,
2. which contract it affects,
3. how determinism is preserved,
4. whether capability authority changes,
5. which tests prove the behavior,
6. whether documentation must change.

Keep unrelated refactors separate.

## Security-sensitive changes

Changes to capabilities, filesystem boundaries, process execution, environment inheritance, HTTP access, dynamic code execution, or privilege boundaries require explicit security review.

See `SECURITY.md`.
