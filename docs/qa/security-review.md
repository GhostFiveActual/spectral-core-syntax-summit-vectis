<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# VECTIS Security Review

This review covers the public VECTIS language/compiler/runtime, packaged Studio, and filesystem/process/HTTP capability adapters.

## Verified architectural properties

* Runtime language evaluation does not use Python `eval` or `exec`.
* Process execution does not use `shell=True`.
* String command arguments are rejected by the process adapter.
* Parent environment variables are not inherited implicitly by the process adapter.
* Filesystem paths are constrained to canonical allowed roots.
* HTTP requests remain behind an explicit adapter boundary.
* Unavailable capabilities are denied.
* Execution graph node kinds remain a closed enum.
* Graphs reject cycles and unknown edge endpoints.
* Studio has no external CDN dependency.
* Studio JavaScript avoids dynamic code execution and HTML injection for result rendering.
* Studio defaults to loopback-only binding.

## 0.1 additions

The deterministic expression evaluator supports pure scalar operations and a closed built-in registry. Unknown function names and invalid arity are rejected during semantic analysis.

Assertions fail closed at runtime and gate subsequent nodes in their block.

All changes to evaluator semantics, capabilities, adapter authority, Studio binding behavior, or process/filesystem/network boundaries require regression tests before release.
