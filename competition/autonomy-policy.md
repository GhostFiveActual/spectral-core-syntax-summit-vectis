# Spectral Core Autonomous Engineering Policy

Spectral Core may autonomously:

- inspect this repository
- create and modify project code
- create and modify project documentation
- create tests
- run tests and static checks
- diagnose failures
- repair its own changes
- perform architecture reviews
- perform security reviews
- perform accessibility reviews
- commit validated work
- continue through the approved backlog

Spectral Core may not autonomously:

- modify files outside this repository
- modify this policy
- modify project provenance
- modify the competition manifest
- push Git commits to a remote
- submit to Devpost
- create external accounts
- use credentials or secrets
- install operating-system packages
- invoke sudo
- rewrite Git history
- force-push
- disable or weaken tests merely to pass
- execute arbitrary model-generated shell commands
- claim behavior that has not been implemented and tested

All model-generated files are untrusted until deterministic validation passes.

A second specialist review is required before a task may be marked complete.
