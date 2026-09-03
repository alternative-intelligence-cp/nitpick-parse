# Cycle 0.6 — TOML

**`src/format/toml.npk` and `src/emit/toml.npk`: TOML v1.0.0, complete.** The
format with the hardest semantics in the 1.0 set, and the one that brings a
second, independent oracle with it.

## Why it is a whole cycle

Not the lexing — TOML's tokens are easy. **The table-header semantics.**
`[a.b.c]` implicitly creates `a` and `a.b`; `[[x]]` appends to an array of
tables; a dotted key inside an inline table cannot escape it; a table defined
after a dotted key already created it is an error; and a key defined in a table
already closed by a later header is an error. Every one of those is a
`toml-test` case, and getting them right is most of the cycle.

## Decisions in

PA-050, PA-053, PA-054, PA-060. All settled.

**Open by design:** O-P4 (the `ntime` overlap) — TOML's four date-time types are
**scanned and classified, never interpreted** (`FORMATS.md` R-9), and the
recommendation is that it stays that way. Nothing in this cycle is blocked on
it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.6.0 | **The corpus** — toml-test vendored, both sets, the expected-JSON encodings | the `corpus` stage judging both directions |
| 0.6.1 | **Scalars** — the four bases, floats, strings in four flavours, the four date-time types | every literal form in the specification |
| 0.6.2 | **Keys and tables** — bare, quoted, dotted; the header semantics | every `toml-test` table case |
| 0.6.3 | **Arrays of tables and inline tables** — the two composite forms | the containment rules |
| 0.6.4 | **The writer** — the canonical form | the round trip green over `valid/` |
| 0.6.5 | **Close** | `done/0.6/`, `0.7.0.md` written |

## Checklist

### 0.6.0 — the corpus
- [ ] toml-test vendored with `PROVENANCE.md`, both `valid/` and `invalid/`
- [ ] the `corpus` stage judging `valid/` as accepted and `invalid/` as faulted, with an **exact** pass count
- [ ] **the expected-JSON second oracle** (R-12): every `valid/` case's tree printed as JSON and compared to the corpus's own expected encoding — **the only check in the suite that does not go through our own reader**
- [ ] the specification version pinned in `meta/research/format-versions.md` (PA-054) — "TOML" without a version is three incompatible languages

### 0.6.1 — scalars
- [ ] integers in base 10, 16, 8 and 2, with underscores, through `arith.npk` (PA-012)
- [ ] floats including `inf`, `-inf`, `nan`, exponents, and the underscore rules
- [ ] basic strings, multi-line basic, literal strings, multi-line literal — with the line-ending-backslash and leading-newline trimming rules
- [ ] `\U0001F600`-style eight-digit escapes through `scan_hex8`
- [ ] the four date-time types **scanned, classified and not interpreted** (R-9): offset date-time, local date-time, local date, local time. `ScalarKind` carries which; the node keeps the text
- [ ] a test asserting `nparse` does **not** reject 31 February — that is `ntime`'s question, and the module header says so

### 0.6.2 — keys and tables
- [ ] bare, quoted and dotted keys
- [ ] `[a.b.c]` creating `a` and `a.b` implicitly
- [ ] redefinition as `Fault(BadTable)` — **and `DupPolicy` does not relax it** (D-15), asserted
- [ ] a key in a table closed by a later header as `Fault(BadTable)`
- [ ] a dotted key that would escape an inline table refused
- [ ] every `toml-test` table case green, and the ones that are subtle listed in the record with what they taught

### 0.6.3 — arrays of tables and inline tables
- [ ] `[[x]]` appending; mixing `[[x]]` with `[x]` refused
- [ ] inline tables immutable after definition, and their newline rules
- [ ] deep nesting of both, bounded by `NPARSE_MAX_DEPTH`

### 0.6.4 — the writer
- [ ] the canonical form from `specs/WRITER_MODEL.md` §3: tables in document order, bare keys where the grammar allows, shortest base-10 integers, no blank lines inside a table
- [ ] `EParseEncode` for what TOML cannot represent: a top-level scalar, a top-level array, a non-string key, a `null`
- [ ] the round trip green over the whole `valid/` set

## Gate

`toml-test` green in both directions with an exact count, **and** the
expected-JSON oracle agreeing on every `valid/` case — two independent judges,
one of which never touches our reader.

## Watch for

- **The table semantics are where the cycle goes long.** Budget for them and
  work case-by-case from the corpus rather than from the specification prose;
  the corpus encodes distinctions the prose leaves implicit.
- **`raw` is a keyword and TOML says "raw string" constantly.** `lit` is the
  spelling this library uses (`specs/BUILD.md` §7).
- **Do not interpret dates.** The pull toward validating them is strong,
  `ntime` does not exist, and a half-validating date parser inside a parsing
  library is exactly how the duplication this library exists to end starts
  again (O-P4).
