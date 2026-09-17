# VECTIS Threat Model

## Assets

The primary assets protected by VECTIS are:

- host files and project data;
- process-execution authority;
- network-access authority;
- execution-graph integrity;
- deterministic language semantics;
- capability declarations;
- repository history and protected records; and
- autonomous-controller state.

## Trust boundaries

### Source to compiler

VECTIS source is untrusted input until it passes lexical, syntactic, and
semantic validation.

The parser does not interpret arbitrary Python. The compiler translates
the validated AST into the VECTIS execution graph.

### Graph to runtime

The execution graph is typed. `NodeKind` is closed rather than accepting
arbitrary strings.

Runtime operations remain subject to capability checks and explicit
handlers.

### Runtime to adapters

Filesystem, process, and HTTP side effects cross an explicit adapter
boundary.

Adapters are responsible for enforcing the narrower authority granted to
each external operation.

### Autonomous model to repository

Model-generated content is untrusted until transport validation,
task-file boundary validation, task acceptance, and repository quality
checks succeed.

Repeated deterministic failures place the controller into a persistent
blocked state.

## Threats and controls

### Arbitrary command execution

Threat: DSL or generated data becomes shell syntax.

Controls:

- structured process arguments;
- rejection of string commands;
- executable allowlisting;
- rejection of relative executable allowlist entries; and
- no `shell=True` process execution.

### Environment leakage

Threat: child processes inherit unrelated host secrets or configuration.

Control: the process adapter does not implicitly inherit the parent
environment.

### Filesystem authority escape

Threat: a workflow accesses data outside its intended filesystem
authority.

Control: filesystem effects are mediated by the filesystem adapter and
its configured path authority.

### Network authority expansion

Threat: a workflow silently gains unrestricted network behavior.

Controls:

- explicit HTTP adapter;
- capability-mediated runtime authority;
- HTTP/HTTPS policy;
- bounded timeouts;
- disabled implicit proxies; and
- disabled redirects.

### Capability bypass

Threat: execution proceeds without required authority.

Controls:

- explicit capability declarations and registry;
- capability checks before protected execution; and
- denial of unavailable capabilities.

### Graph-type injection

Threat: arbitrary strings create new execution semantics.

Control: `NodeKind` is a closed enumeration and rejects unknown values.

### Dynamic-code injection

Threat: VECTIS content is evaluated as Python.

Controls:

- deterministic parser/compiler pipeline; and
- runtime implementation does not use Python `eval()` or `exec()` for
  VECTIS execution.

### Autonomous repair loop

Threat: a failing model repeatedly mutates the repository indefinitely.

Controls:

- bounded repair counter;
- persistent `blocked` state at the threshold;
- blocked-task and block-reason recording;
- clean process exit; and
- startup refusal while blocked.

### Repository corruption

Threat: autonomous work modifies unrelated or protected artifacts.

Controls:

- task file boundaries;
- deterministic quality gates;
- protected project records;
- clean-worktree checks;
- preservation of task WIP for diagnosis; and
- no autonomous push.

## Residual threats

No local software control eliminates risk from vulnerabilities in the
host operating system, Python runtime, external network services, or
authorized executables themselves.

Adapter policy and capability policy therefore remain security-critical
configuration and must not be widened implicitly.

## Review rule

A change that expands filesystem, process, HTTP, capability, runtime, or
controller authority requires corresponding security tests and threat
model review before final release.
