# Cycle 0.3 — JSON

**`src/format/json.npk`: RFC 8259, complete.** Plus the two instruments that
make it more than one format — `plugin_conform`, and the trivial fifth format
that proves nothing in the library knows the shipped ones are special.

## Why JSON first

It is the smallest complete specification with the best conformance corpus. That
combination means the **path** — scanner to events to conformance harness to
corpus — is proven on the format least likely to confuse a path problem with a
format problem. TOML's table semantics and YAML's indentation are both harder
than anything in JSON, and debugging the shared machinery through either would
be debugging two things at once.

## Decisions in

PA-050, PA-053, PA-054, PA-070, PA-072, PA-081. All settled.

**Open questions to settle:** O-P2 (`NPARSE_MAX_SCALAR`) — a *measurement*,
taken here against the corpus and a realistic large document. O-P1 (the
duplicate-key default) is confirmed here against JSONTestSuite, though it lands
in 0.4 with the document.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.3.0 | **The corpus** — JSONTestSuite vendored, `PROVENANCE.md`, the `corpus` stage | the stage judging cases and its pass count exact |
| 0.3.1 | **The reader** — values, strings, numbers, containers | the whole RFC 8259 grammar |
| 0.3.2 | **`plugin_conform`** — the eight obligations, mechanically | JSON green under all eight |
| 0.3.3 | **The trivial fifth format** — in `tests/`, proving the path a third party takes | `plugin_conform` green over it too |
| 0.3.4 | **JSON Lines** — the option, not a format | a 1 GB file streamed in constant memory |
| 0.3.5 | **Close** | `done/0.3/`, `0.4.0.md` written |

## Checklist

### 0.3.0 — the corpus
- [ ] JSONTestSuite vendored under `tests/corpus/jsontestsuite/` with a `PROVENANCE.md` naming the upstream repository, commit hash and date (PA-081)
- [ ] `check_corpus_provenance` live: the vendored tree's hash matches what `PROVENANCE.md` records
- [ ] the `corpus` stage: every `y_` accepted, every `n_` faulted, every `i_` producing a **recorded verdict** in a committed file (V-10)
- [ ] the pass count **exact**, and an unexpected *improvement* failing the run (B-9) — the self-check's pending case 8 goes live here, both directions
- [ ] **a build never fetches** — the vendoring script is in `tools/` and refuses to run during a build

### 0.3.1 — the reader
- [ ] objects, arrays, strings with all escapes, numbers, `true`, `false`, `null`
- [ ] UTF-8 required and validated (PA-013, RFC 8259 §8.1)
- [ ] every number form: integer, fraction, exponent, all sign combinations, and the leading-zero and bare-`.` rejections
- [ ] `EV_BIG` on a literal exceeding 64 bits, and the literal still **accepted** (PA-033) — a 40-digit integer is valid JSON
- [ ] a lone surrogate is `Fault(UnpairedSurrogate)` (`SCAN_MODEL.md` C-23)
- [ ] a leading BOM stripped when `allow_bom`, and RFC 8259's prohibition noted in the module header
- [ ] `Fault(TrailingContent)` after the value
- [ ] **the extensions are not implemented and not enabled**: no comments, no trailing commas, no unquoted keys, no single quotes, no `NaN`/`Infinity` (R-5) — with a test asserting each is refused
- [ ] O-P2 measured: the largest scalar in the corpus and in a realistic large document, and `NPARSE_MAX_SCALAR` recorded with the measurement

### 0.3.2 — `plugin_conform`
- [ ] `plugin_conform<F: Format>(make, corpus)` checking all eight obligations from `specs/PLUGIN_MODEL.md` §3 mechanically, with the table in §5 as the implementation guide
- [ ] the termination check specifically: a step counter bounded at `4 × input length`, so a step that returns `Ev` without advancing fails rather than hangs
- [ ] the span-coverage check: the sum of reported spans plus deliberate skips equals the input
- [ ] the scratch high-water check, under `NPARSE_MAX_SCALAR`
- [ ] JSON green under all eight, over the whole corpus

### 0.3.3 — the trivial fifth format
- [ ] a deliberately minimal `Format` in `tests/` — a newline-separated list of bare words, say — implementing the trait and nothing else
- [ ] it imports **only** what the library exports, uses no privileged entry point, and is registered nowhere
- [ ] `plugin_conform` green over it
- [ ] `doc_build` works on it unchanged (pending until 0.4, written now)
- [ ] **this is the test of PA-070's claim** and it runs on every full run, so the path a third party takes is walked continuously rather than asserted once

### 0.3.4 — JSON Lines
- [ ] `json_lines_reader` emitting `DocStart`/`DocEnd` per line (R-6)
- [ ] a 1 GB JSON Lines file consumed through the event path with **allocation constant in the input size**, measured — the first evidence for `EVENT_MODEL.md` E-25, which cycle 0.10 turns into a gate
- [ ] a line that is malformed faults **without** ending the stream, if `max_errors` permits — the first exercise of recovery's shape, ahead of 0.9

## Gate

JSONTestSuite green with an exact pass count and recorded `i_` verdicts, and
`plugin_conform` green over **both** JSON and the trivial fifth format.

## Watch for

- **The `i_` verdicts are the valuable half.** The implementation-defined cases
  are where parsers diverge, and recording our answer for each is how a future
  change to a number or an escape rule becomes visible rather than discovered.
- **Do not let JSON's simplicity hide a path problem.** If something is awkward
  here it will be worse in TOML and YAML — the friction is a finding about the
  shared layer, not about JSON, and it belongs in the record.
- **The trivial format is not a toy.** It is the only mechanical evidence that
  the plugin claim is true. Writing it as an afterthought defeats its purpose;
  write it before JSON is finished, so JSON does not accidentally acquire a
  privilege.
