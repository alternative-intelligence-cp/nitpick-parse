# `src/diag/` — diagnostics

`ParseError`: a closed code enum, a span, an expected set, and a renderer.
A syntax error is a **value** carried in the success channel, never an `error:`
identity — `meta/specs/SAFETY.md` §3 is why. Governed by
`meta/specs/DIAGNOSTIC_MODEL.md`. Built alongside cycle 0.2 and completed in
0.9.
