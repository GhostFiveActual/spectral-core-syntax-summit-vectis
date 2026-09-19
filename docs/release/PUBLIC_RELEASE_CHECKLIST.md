<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Public Release Checklist

Target: **v0.1.0 public preview**

## Required before public release

* [ ] Choose and add an explicit software license.
* [ ] Decide whether the final public repository will remain `spectral-core-syntax-summit-vectis` or move to a short product repository such as `GhostFiveActual/vectis`.
* [ ] Run CI on Python 3.11, 3.12, 3.13, and 3.14.
* [ ] Build wheel and sdist from the release candidate.
* [ ] Install the wheel into a clean environment outside the source tree.
* [ ] Run `vectis doctor`.
* [ ] Run the canonical CLI demo.
* [ ] Launch installed-wheel `vectis studio` and verify all API/UI panels.
* [ ] Verify no internal autonomous build/provenance paths are present.
* [ ] Verify README and specification match the final version.
* [ ] Review security policy and private vulnerability-reporting configuration.
* [ ] Tag only after all release gates pass.

## Product repository exclusions

The public release should not contain:

```text
.autonomy/
artifacts/
competition/
docs/submission/
tools/spectral_core_controller.py
tools/vectis_task_contracts.py
tools/task-gates/
```

Those materials belong in Ghost Five internal engineering/provenance storage.

## Version policy

`v0.0.1` remains immutable as the engineering baseline. New language/UI work belongs to the `0.1.x` line.
