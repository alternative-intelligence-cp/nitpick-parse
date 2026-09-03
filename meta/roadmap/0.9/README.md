# Cycle 0.9 — Diagnostics and recovery

**`src/diag/` completed: rendering with a caret, the `expected` masks filled in
per format, per-format resynchronisation, and multi-fault collection.**

## Why here

Because recovery needs **every format's resynchronisation rule to exist** before
the shared machinery can be right — there is no format-neutral answer
(`DIAGNOSTIC_MODEL.md` F-10) — and because the `expected` masks are only
meaningful once each format's grammar is written. Doing it earlier would mean
designing against one format and retrofitting three.

And because it is the feature cycle 0.12's linter genuinely exercises: nothing
else in the plan needs a document's twentieth error.

## Decisions in

PA-040, PA-041, PA-042. All settled.

**Open questions to settle:** O-P7 (the third-party fault-code mechanism —
recommendation `FormatSpecific(uint16)`), and O-P3 / O-P10 together (whether
`scan_line_col` should memoise, and whether the renderer should share context
across faults — **one measurement, one answer**).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.9.0 | **Rendering** — `fault_render`, the caret, the code format | a diagnostic a person can act on |
| 0.9.1 | **The `expected` masks** — filled in per format | every fault naming what it wanted |
| 0.9.2 | **Resynchronisation** — the four per-format rules | recovery that does not invent structure |
| 0.9.3 | **Multi-fault collection** — `max_errors`, the fault vector | twenty faults from one document |
| 0.9.4 | **The measurement** — O-P3 and O-P10 | one answer, recorded |
| 0.9.5 | **Close** | `done/0.9/`, `0.10.0.md` written |

## Checklist

### 0.9.0 — rendering
- [ ] `fault_render(f, src, name, sink)` in the compiler's diagnostic shape: `NPARSE-nnnn path:line:col: message`, the source line, the caret
- [ ] **the code is stable and the message is not** (F-14) — every test asserts on the code, never the text
- [ ] `scan_line_col` called **only** here, and the only place a one-based number exists (F-15)
- [ ] **the caret counts codepoints, not display columns**, and the documentation says so (F-16) — `nparse` carries no Unicode width tables and will not, because that is `ntui`'s domain and two copies would be two things to keep in sync
- [ ] a consumer with width tables can render its own caret from the span, which is why the span is what the library guarantees

### 0.9.1 — the `expected` masks
- [ ] `TokenClass` and the mask, filled in at every fault site in all four formats
- [ ] `fault_found_byte` / `fault_found_class` as the only readers of `found` (F-8)
- [ ] every `FaultCode` variant now has a test producing it — `check_codes_documented` fully green for the first time, with no pending rows
- [ ] O-P7 decided and recorded: `FormatSpecific(uint16)` plus a rendering hook, because a reserved band in a closed enum is a band somebody eventually collides in

### 0.9.2 — resynchronisation
- [ ] the four rules from `specs/DIAGNOSTIC_MODEL.md` F-10: JSON at the next `,` or closer at the current depth; TOML at the next line beginning a key or header; CSV at the next record separator; YAML at the next line at or below the current indentation
- [ ] **recovery never invents structure** (F-11) — no fabricated closing brace, asserted
- [ ] `doc_build` returns the fault regardless of recovery (D-22), so a *data* consumer cannot accidentally read a partial document
- [ ] **recovery is not on the round-trip path** (F-12) — the oracle does not run on a recovered parse, and a test asserts the harness refuses to

### 0.9.3 — multi-fault collection
- [ ] `Options.max_errors`, defaulting to 0 (stop at the first)
- [ ] a `Vec<ParseError>` collected up to the bound, then parsing stops and the set is returned
- [ ] `NPARSE_MAX_ERRORS` (64) enforced
- [ ] a deliberately broken document of each format producing a sensible *set* of faults — the test being that the second fault is not merely the wreckage of the first

### 0.9.4 — the measurement
- [ ] O-P3 and O-P10 measured together: render twenty faults from a large document and measure the cost of re-scanning for line starts each time
- [ ] the answer recorded — either "leave it" or "build a line-start index once, on the first diagnostic" — with the numbers behind it

## Gate

A deliberately broken document of each of the four formats producing a set of
faults whose second and later entries are independently useful, each rendered
with a code, a span and a caret.

## Watch for

- **A recovered parse is a diagnostic artifact, not data.** The pull to "return
  what we recovered" is strong and F-11/F-12 refuse it: a document that differs
  from the input in ways nobody chose is worse than a refusal.
- **The second fault is the hard one.** A resynchronisation rule that lands
  inside the construct it was trying to skip produces a cascade, and a cascade
  is worse than a single fault because it buries the real one.
- **Do not grow width tables.** The caret's codepoint counting is a stated
  limitation with a stated reason; adding a table here would duplicate `ntui`'s
  and put two copies of UAX #11 in one ecosystem.
