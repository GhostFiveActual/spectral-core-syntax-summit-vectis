<!-- ghost-five-brand:start -->
<div align="center">

**GHOST FIVE // SPECTRAL CORE // VECTIS**

Deterministic automation. Explicit authority. Inspectable execution.

</div>
<!-- ghost-five-brand:end -->

# Spectral Core Release Standard

## Release principle

A release is a recorded state that can be reproduced and inspected. Published tags are not rewritten.

## Required release evidence

1. Identify the release commit.
2. Pass the repository quality gate.
3. Pass CI on every supported runtime version.
4. Build the package from a clean checkout.
5. Install the built package outside the source tree.
6. Run primary commands from the installed package.
7. Cover security boundaries with regression tests.
8. Match documentation to shipped behavior.
9. Record material changes and known limits.
10. Choose an explicit software license before presenting an open source release as open source.

## Version discipline

Development versions describe work that is not yet a published contract. Release tags identify immutable milestones.

The VECTIS v0.0.1 tag remains the engineering baseline. The 0.1.0.dev0 line is the active public preview development line until the release checklist is complete.

## Release command

The repository should expose one quality gate and one automated release workflow. Manual release steps should be limited to decisions that require human authority, such as approving the final version or license.
