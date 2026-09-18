# VECTIS Security Policy

VECTIS treats external authority as an explicit capability boundary.

## Supported release

The current supported development release is **v0.0.1**.

## Reporting a vulnerability

Do not publish credentials, exploit details, or sensitive deployment information in a public issue.

For a private repository, report the issue directly to the repository owner through the available private GitHub communication channel.

If the repository is later made public, configure GitHub Private Vulnerability Reporting before accepting public security reports.

## Security invariants

Contributions must preserve these principles:

- no implicit shell execution,
- no dynamic `eval` or `exec` runtime path,
- no implicit inheritance of parent process environment,
- explicit executable allowlists for process adapters,
- explicit filesystem containment,
- explicit HTTP scheme and timeout constraints,
- unavailable capability is denied,
- semantic validation occurs before execution,
- execution graphs remain deterministic and acyclic.

Security regressions should include a test that fails without the fix.
