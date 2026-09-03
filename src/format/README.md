# `src/format/` — the shipped plugins

JSON (RFC 8259), TOML (1.0.0), CSV (RFC 4180 plus dialects) and a precisely
defined YAML subset. Each is an ordinary `Format` trait implementation with no
privileged access to anything — a third-party format is written exactly the same
way. Governed by `meta/specs/FORMATS.md`. Built in cycles 0.3, 0.6, 0.7 and
0.8.
