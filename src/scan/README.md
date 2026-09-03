# `src/scan/` — the shared scanning layer

The cursor over `uint8[]`, spans as byte offsets, on-demand line/column, UTF-8
validation, escape decoding into scratch, and **number scanning that cannot
trap** — the rule that keeps an attacker-supplied numeric literal from stopping
the program. Declares no errors. Governed by `meta/specs/SCAN_MODEL.md`. Built
in cycle 0.1.
