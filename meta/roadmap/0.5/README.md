# Cycle 0.5 — The writers and the oracle

**`src/emit/json.npk`, the `EventSink` trait, and the `roundtrip` stage.** The
instrument that judges every format after this one.

## Why before TOML, CSV and YAML

Because an instrument co-developed with the thing it judges tends to agree with
it. Written here, over the format that is already proven, the round trip is a
**working oracle** on the day TOML's first line is written — so the three harder
formats are developed against a checker rather than beside one.

That is the compiler's "instruments precede the constructs they guard", and it
is the same reason `event_validate` came before JSON in 0.2.

## Decisions in

PA-060, PA-061, PA-062, PA-080. All settled.

**Open questions to settle:** none.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.5.0 | **The canonical JSON writer** — the form, the escape set, the numbers | deterministic bytes for a given document |
| 0.5.1 | **The `EventSink` trait** — the streaming writer, the transcode loop | a format-to-format transcode in constant memory |
| 0.5.2 | **The `roundtrip` stage** — the harness leg, `--record-golden` | the two pending self-check cases go live |
| 0.5.3 | **`EmitOpts`** — pretty-printing that does not change the canonical form | one canonical form, options beside it |
| 0.5.4 | **Close** | `done/0.5/`, `0.6.0.md` written |

## Checklist

### 0.5.0 — the canonical JSON writer
- [ ] the canonical form from `specs/WRITER_MODEL.md` §3, exactly: no insignificant whitespace, minimal escapes, shortest round-tripping numbers, members in document order
- [ ] **the escape set is minimal and stated** (W-9): `"` and `\` and `U+0000`…`U+001F`, with the five short forms; **not** `/`, **not** `\u` for non-ASCII. Each of those three divergences has a test asserting we do not do it
- [ ] numbers through the prelude's shortest-round-trip Dragon4 (D-193), **not** a second implementation (W-7)
- [ ] `ND_BIG` written verbatim from its retained text (W-8)
- [ ] `-0` written as `-0`, asserted through a full round trip (E-9)
- [ ] **an explicit stack**, not recursion (W-4) — a 50 000-deep document printed and freed, exiting 0
- [ ] `EParseEncode` for what JSON cannot represent: a `Date` scalar, a NaN, a non-string map key — the second of the library's two error identities, and a **caller** mistake
- [ ] the writer is deterministic: the same document printed twice is byte-identical, asserted

### 0.5.1 — the `EventSink` trait
- [ ] `trait:EventSink = { func:put = NIL(Self->:self, Event:e, uint8[]:text); func:finish = NIL(Self->:self); };`
- [ ] `text` passed alongside because a sink has no parser to resolve a `TextRef` against (W-14) — the caller's one obligation, one line
- [ ] the sink maintains its own depth stack, mirroring the reader
- [ ] **the transcode loop** from `specs/WRITER_MODEL.md` W-15, as a working example in `examples/`: ten lines, constant memory, any format to any format
- [ ] the sink is a `Bytes`, never a `Writer` — `nparse` performs no I/O (W-3)

### 0.5.2 — the `roundtrip` stage
- [ ] the stage: parse, print, parse, compare trees with `doc_eq`, **and** print again and compare bytes (V-7)
- [ ] `// expect-roundtrip: json` as the marker
- [ ] **every corpus case that parses is a round-trip case** (W-12) — the oracle's coverage is the corpus's, for free
- [ ] `--record-golden` as a deliberate act, refused during an ordinary run
- [ ] the self-check's pending cases 6 and 7 go live: a second parse that differs, **and** trees that match with bytes that differ — the second is what proves V-7 is doing work
- [ ] the whole JSONTestSuite `y_` corpus green through the round trip

### 0.5.3 — `EmitOpts`
- [ ] indentation, a trailing newline, key sorting — **as options**
- [ ] **the canonical form is the one with no options set** (W-6), and it is the only one the oracle uses; two forms would be two things to test
- [ ] a test asserting an option changes the bytes and **not** the parsed tree

## Gate

The round trip green over the whole `y_` corpus, with the **second print
byte-identical to the first** — and the self-check's case 7 failing as it must,
proving the byte comparison is not decorative.

## Watch for

- **This is the cycle that makes every later cycle cheaper.** A format that
  passes its corpus and fails the round trip has been *accepted and
  misunderstood*, which is the class no corpus finds. Getting the oracle right
  here pays for itself three times over in 0.6, 0.7 and 0.8.
- **The differential test (0.4.5) and the round trip are not redundant.** A
  symmetric bug in the builder and the writer cancels under the round trip and
  is caught by the differential test; a reader misunderstanding is caught by the
  round trip and not by the differential test. Both, always.
- **`EParseEncode` is a caller mistake, not a fault.** A caller who asked for
  JSON and handed us a TOML date made a choice; that is why it is an identity
  rather than a `Fault` value, and it is the only place in the library where
  that is true of something the *data* triggered.
