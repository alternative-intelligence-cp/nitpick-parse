# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1) and zero-dependency governs the artifact, not the
workbench. It retires into `npkg` the way `bootstrap/harness/` does in the
compiler repository, with both running side by side and a parity check first.
Built in cycles 0.0.2 and 0.0.3.

*(2026-10-15, cycle 0.0.1:)* until cycle 0.0.2, `run.py` is a stub that builds and judges nothing
and says so; CI runs it so that the workflow's last step exists before the runner does.
