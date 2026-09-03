# Cycle 0.2 — The event contract

**`src/event/` and `src/diag/`: `Event`, `Step`, `ParseError`, `TextRef`,
`Options`, the `Format` trait, the depth stack, and `event_validate`.** The
interface the whole library is built around and the one a third party
implements.

## Why here

Because every format is written against it and nothing above it can be designed
until it is fixed. And because `event_validate` — the wrapper that asserts the
stream grammar — must exist **before** the first format, so that JSON is
developed against a checker that already works rather than co-developed with its
own judge. That is the compiler's "instruments precede the constructs they
guard", applied.

## Decisions in

PA-008, PA-009, PA-020 … PA-025, PA-040 … PA-042, PA-071. All settled.

**Open questions to settle:** none. **Open by design:** O-P5 (comment position)
and O-P6 (incremental feeding) both wait for evidence — O-P5 for a formatter,
O-P6 for cycle 0.10's measurement — and **neither changes the contract this
cycle freezes**.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0 | **The vocabulary** — `Event`, `EventKind`, `ScalarKind`, `TextRef`, the flags | 24 bytes, POD, asserted; the closed enums |
| 0.2.1 | **`Step` and `ParseError`** — the fault value, the code enum, the `expected` masks | 24 bytes, POD, asserted; `pick` exhaustiveness demonstrated |
| 0.2.2 | **The `Format` trait and `Options`** — the pull interface, the option checks | a trivial format implementing it, statically and through `dyn` |
| 0.2.3 | **The depth stack** — `Frame`, preallocation, the bound | 50 000 nesting handled, `DepthExceeded` at the bound |
| 0.2.4 | **`event_validate`** — the grammar wrapper | each of the six grammar violations caught |
| 0.2.5 | **Close** | `done/0.2/`, `0.3.0.md` written |

## Checklist

### 0.2.0 — the vocabulary
- [ ] `Event` is exactly 24 bytes; `#size_of` asserted (probe 02's shape made permanent)
- [ ] **no owning field** — `check_no_owning_fields` goes live here
- [ ] `EventKind`'s nine and `ScalarKind`'s nine, both closed (PA-025), with a comment saying adding one is a major version
- [ ] `TextRef { src, lo, hi }` and `event_text(p, e) -> uint8[]`, returning a borrow
- [ ] the four flags: `EV_ESCAPED`, `EV_BIG`, `EV_NEG`, `EV_EMPTY`
- [ ] `-0` survives: `EV_NEG` with a zero magnitude, asserted through a round trip in 0.5

### 0.2.1 — `Step` and `ParseError`
- [ ] `Step = { Ev(Event); Fault(ParseError); Done; }` (probe 03's shape)
- [ ] `ParseError` exactly 24 bytes, POD, `#size_of` asserted
- [ ] the `FaultCode` enum, every variant in `specs/DIAGNOSTIC_MODEL.md` §3
- [ ] `check_codes_documented` live: every variant in the spec table, every one with a test that produces it (most pending until their format lands, and **pending must print as pending**)
- [ ] the `expected` bitmask over `TokenClass`
- [ ] `fault_found_byte` / `fault_found_class` as the **only** way to read `found` (F-8's D-069 compromise)
- [ ] a rejection test proving a non-exhaustive `pick` over `Step` **does not compile** — the mechanism PA-008's whole argument rests on, asserted rather than assumed

### 0.2.2 — the `Format` trait and `Options`
- [ ] `trait:Format = { func:step = Step(Self->:self); };`
- [ ] a trivial format in `tests/` implementing it — the one that becomes `PLUGIN_MODEL.md` G-8's proof in 0.3
- [ ] driven statically through a bound, and through `dyn Format` (probe 07's shape)
- [ ] `Options` with every field and `options_default()` (G-12: struct literals must be complete, so the constructor is the compatible path)
- [ ] **an incoherent option is `EParseState` at construction**, not a surprise at step 4000 (E-21) — asserted for `max_depth == 0` and `max_scalar == 0`
- [ ] `step` idempotent after `Done` and after `Fault` (PA-024), asserted by calling three more times
- [ ] `check_error_budget` confirming exactly two identities exist

### 0.2.3 — the depth stack
- [ ] `Frame { kind, count, span }`, `Vec<Frame>`, **preallocated to the bound** (E-16)
- [ ] `check_no_recursion` live and biting — every function in `src/` checked against a call-graph cycle, exceptions table empty
- [ ] 50 000 nesting handled without touching the machine stack (probe 10's shape made permanent)
- [ ] `Fault(DepthExceeded)` at exactly the bound, with the span of the container that would have opened
- [ ] the bound is a per-parse option and the default is 128

### 0.2.4 — `event_validate`
- [ ] a wrapper `Format` asserting `specs/EVENT_MODEL.md` §3's grammar on every step
- [ ] each of the six violations caught, proven by a **deliberately broken** test format: a value after `Done`, a `Key` not followed by a value, an `EndMap` closing a `StartSeq`, an unbalanced open, a `Key` outside a map, a `Scalar` between `Key` and its value
- [ ] the unwind rule (E-11): after a `Fault`, open containers are not required to close, and a consumer must not assume balance
- [ ] documented as the thing a plugin author develops against, and **off in production** because it costs a state machine per step

## Gate

`event_validate` catches all six grammar violations, and a non-exhaustive `pick`
over `Step` fails to compile — the two mechanisms PA-008 and E-13 rest on,
demonstrated rather than asserted.

## Watch for

- **`error` is a keyword and `Fault` is the word this library uses**
  (`GLOSSARY.md`). The distinction between a *fault* (a value, from input) and
  an *error* (an identity, from misuse) is the library's central design
  decision, and letting the vocabulary blur is how it gets eroded.
- **`Event` having no owning field is not negotiable.** If the 24 bytes turn out
  too tight, the answer is a wider `Event` or a narrower `TextRef` — never a
  `string`.
- **Design the ring for push-back now.** The capability probe pattern (a
  consumer reading events until a sentinel and pushing the rest back) is not
  needed by any format here, but `Options` and the driver shape should not
  foreclose it.
