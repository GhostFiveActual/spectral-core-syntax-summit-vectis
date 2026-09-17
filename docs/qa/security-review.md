# VECTIS Architecture and Runtime Security Review

## Scope

This review covers the deterministic VECTIS language pipeline, execution
graph, capability model, runtime, filesystem adapter, process adapter,
HTTP adapter, and autonomous engineering controller.

The review focuses on trust boundaries, authority, deterministic
execution, external side effects, unsafe process behavior, network
behavior, failure handling, and preservation of repository state.

## Security model

VECTIS separates language authoring from execution authority.

Source text is accepted by the lexer and parser, checked by semantic
analysis, compiled into a deterministic execution graph, and then
executed through the runtime. External effects are exposed through
explicit adapters rather than arbitrary language-level code execution.

An LLM may author or repair source and repository artifacts, but it does
not define language semantics. The deterministic lexer, parser, semantic
analyzer, compiler, runtime, task gates, repository quality gate, and
adapter policies remain authoritative.

## Capability boundary

Capabilities provide an explicit authority boundary between an execution
graph and runtime effects.

Capability declarations are represented by the capability registry.
Unavailable required capabilities are denied by the runtime. Capability
denial remains a specialized capability error so callers can handle
denial without weakening the general capability-error contract.

The capability model must remain fail-closed. Unknown or unavailable
authority must not become implicitly available.

## Process execution

The process adapter uses structured command arguments and an explicit
executable allowlist.

Security requirements include:

- string commands are rejected;
- relative executable allowlist entries are rejected;
- command arguments are preserved without shell interpolation;
- the parent environment is not implicitly inherited;
- standard output and error are captured;
- execution timeouts are bounded; and
- nonzero process exit is represented as a structured result.

The security suite also verifies that the implementation does not enable
`subprocess` with `shell=True`.

## Filesystem access

Filesystem effects are isolated behind the filesystem adapter rather
than being exposed as unrestricted runtime operations.

Paths must remain subject to the adapter's configured authority and
normalization rules. Filesystem policy should continue to treat path
escape, unintended authority expansion, and unsafe external effects as
security failures rather than convenience fallbacks.

## HTTP access

HTTP effects are isolated behind the HTTP adapter.

The current adapter design uses the standard-library HTTP stack, limits
requests to HTTP/HTTPS behavior, disables implicit proxy behavior and
redirect behavior, and applies timeout and transport/status handling.

Network access remains an explicit capability rather than an implicit
property of VECTIS programs.

## Execution graph and runtime

`NodeKind` is a closed enumeration. The runtime consumes typed graph
nodes rather than arbitrary user-selected node-kind strings.

The runtime performs deterministic scheduling, tracks node state, denies
unavailable capabilities, supports dry-run execution, and propagates
failures to dependent work.

The security review verifies that the runtime does not use Python
`eval()` or `exec()` to implement VECTIS semantics.

## Autonomous engineering controller

The controller is not part of VECTIS language semantics, but it is a
security boundary for autonomous repository modification.

Important controls include:

- task-scoped output paths;
- syntax validation before generated Python is accepted;
- VECTIS source validation before generated VECTIS reaches the worktree;
- deterministic task and repository quality gates;
- no automatic push;
- preservation-first rollback behavior; and
- a persistent autonomy block after the repair-failure threshold.

After repeated deterministic failure, the controller saves
`blocked=true`, records the blocked task and reason, and exits cleanly.
Startup checks the persistent block before model selection. Because the
systemd unit uses `Restart=on-failure`, a clean blocked exit prevents a
restart loop.

## Findings

No architecture change is required to permit unrestricted shell
execution, unrestricted filesystem access, arbitrary node kinds, or
implicit capabilities. Those behaviors would weaken the existing
security model and should remain prohibited.

The security-relevant regression suite verifies selected controls
against the existing process-adapter and runtime tests rather than
reimplementing those controls in a parallel test harness.

## Residual risk

Security depends on preserving adapter boundaries, capability checks,
task gates, and deterministic validation as the language evolves.

Future changes to adapters, graph metadata, process execution, HTTP
behavior, capability resolution, or autonomous-controller permissions
should update this review and add regression coverage before release.

## Contract vocabulary

`deny`


## Threat assessment

The security threat assessment treats capability authorization,
filesystem access, process execution, and HTTP access as explicit trust
boundaries. The runtime must deny operations when required authority is
not available, and each threat that could expand authority must remain
constrained by deterministic validation, capability checks, adapter
policy, and fail-closed controller behavior.
