# `tests/`

| Directory | Stage | Contents |
|---|---|---|
| `probe/` | `program` | the cycle-0.0 language probes; **never deleted** |
| `conformance/` | `accept` | the public API compiles in a program that only imports it |
| `unit/` | `program` | behaviour, judged by exit code |
| `roundtrip/` | `roundtrip` | parse -> print -> parse fixed-point cases |
| `rejection/` | `check` | programs the compiler must refuse, with exactly the expected codes |
| `fixtures/` | `program` | inputs that once found a defect, kept permanently |
| `corpus/` | `corpus` | the VENDORED conformance corpora, with their upstream commits in `PROVENANCE.md` |

Expectations live in the test file. Governed by `../meta/specs/TESTING.md`.
