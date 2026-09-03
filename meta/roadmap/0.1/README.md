# Cycle 0.1 — Scan

**`src/scan/`: the cursor, spans, byte classes, UTF-8, escape primitives, and
`arith.npk`.** The layer every format shares, and the reason this library
exists — what the prototype's five parsers each rewrote was not the grammar, it
was this.

> **`0.1.0.md` is written execution-grade at cycle 0.0's close** (0.0.5, step
> 4), so this cycle is openable by a session that was not present for the
> probes. That is the convention for every cycle.

## Why here, and why it is the riskiest cycle in the plan

Because **`arith.npk` is where the library's central claim lives**. PA-012 says
no arithmetic may trap on any input; probe 01 demonstrated the hazard and the
shape of the answer; this cycle turns that shape into the three helpers every
numeric scan in every format will route through. Get it wrong here and every
format built on it has a remote denial of service.

Everything else in the cycle is pure computation over bytes with no I/O, no
allocation beyond a scratch, and no state, so it is the cycle with the cleanest
tests in the plan — which is exactly why the dangerous part deserves the
attention.

## Decisions in

PA-010 … PA-014, and PA-004's `limits.npk`. All settled.

**Open questions to settle:** none. **Open by design:** O-P2
(`NPARSE_MAX_SCALAR`) is a *measurement*, taken at cycle 0.3 against the
JSONTestSuite corpus, not here.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.1.0 | **`arith.npk`** — the three checked helpers, and nothing else | the worst-case gate green, and `check_no_raw_accumulate` biting |
| 0.1.1 | **The cursor and spans** — the total operations, `Span`, `scan_line_col` | every operation total, no input producing anything but a clamp |
| 0.1.2 | **Byte classes** — the generated 256-byte table and its predicates | the table regenerating byte-identically |
| 0.1.3 | **UTF-8** — the decoder, Table 3-7 exactly | every boundary of every sequence length |
| 0.1.4 | **Escape primitives** — `scan_hex4`, `scan_hex8`, surrogate pairing, the scratch | an unpaired surrogate refused, not substituted |
| 0.1.5 | **Number scanning** — `NumInfo`, classification without materialisation | a 5000-digit literal classified, not evaluated |
| 0.1.6 | **Close** | `done/0.1/`, `0.2.0.md` written |

## Checklist

### 0.1.0 — `arith.npk`
- [ ] `scan_mul_add(acc, base, digit, bound) -> uint64?` with the guard order from `specs/SCAN_MODEL.md` §5, exactly: `base == 0` first, `digit > bound` second, then the division, then the comparison
- [ ] `scan_add(a, b, bound) -> uint64?` and `scan_shift(acc, bits, bound) -> uint64?`
- [ ] **the worst-case gate**: a program feeding each helper its adversarial inputs — 5000 digits, `bound` at `UINT64_MAX`/`INT64_MAX`/`0`/`1`, `base` at 2/8/10/16 and 0, `digit` at 0 and at `bound` and at `bound+1` — that **exits 0**, proving no path traps
- [ ] the same program run under `opt -O2` with the same exit (B-3), because an optimiser that hoisted a multiply above a guard would be exactly the defect this cycle exists to prevent
- [ ] `check_no_raw_accumulate` live over `src/scan/` and **seen to fail** against a planted naive accumulator
- [ ] the four internal facts written as `prove` comments in the syntax they will take (`specs/VERIFICATION.md` §4)
- [ ] a property test standing in for each, over a swept input space

### 0.1.1 — the cursor and spans
- [ ] `Cursor { uint8[]:src; int64:pos; }` and the seven total operations from `specs/SCAN_MODEL.md` C-3
- [ ] **every operation total**: an out-of-range position clamps, never traps, never returns garbage — asserted at `pos == 0`, `pos == len`, `pos > len`
- [ ] `Span { uint32:lo; uint32:hi; }`, half-open, with `lo <= hi` maintained
- [ ] an input longer than `0xFFFFFFFF` refused at entry with `EParseState` (C-5) — a caller mistake, not an input's
- [ ] `scan_line_col(src, offset)` counting from the start, one-based, and **the only place a one-based number exists**
- [ ] the `Cursor`-holding-a-borrow shape from probe 08's fourth edge, exercised at every call depth the formats will use

### 0.1.2 — byte classes
- [ ] a generated `uint8[256]` class table, committed as source, regeneration-checked
- [ ] `is_space`, `is_newline`, `is_digit`, `is_hex_digit`, `is_alpha`, `is_alnum`, `is_control`, `is_ascii` — each total over all 256 values, each asserted over all 256
- [ ] `check_tables_regenerate` live for this table (the first generated file in the tree)

### 0.1.3 — UTF-8
- [ ] the decoder accepts exactly Unicode Table 3-7: no overlongs, no surrogates, nothing above `U+10FFFF`, per-lead-byte continuation ranges
- [ ] `scan_utf8(c) -> Optional<Utf8Step>` returning `NIL` on ill-formed input, with **no policy** — reject-or-substitute is the format's (C-11)
- [ ] a corpus test over every boundary of every sequence length, including the four overlong forms and both surrogate halves
- [ ] the codepoint accumulation goes through `arith.npk` like everything else (C-12), even though a four-byte sequence cannot overflow a `uint32` — because the rule admits no exceptions and an unchecked accumulation is something a reader has to reason about
- [ ] a `prove` comment: the length is 1…4 and the codepoint is a scalar value

### 0.1.4 — escape primitives
- [ ] `scan_hex4`, `scan_hex8`, both through `arith.npk` with their bounds (`0xFFFF`, `0x10FFFF`)
- [ ] surrogate pairing, and **an unpaired surrogate is a fault, never a substitution** (C-23) — asserted both halves, both orders, and a high surrogate at end of input
- [ ] the scratch: `Bytes`, cleared per scalar, so its lifetime is one event
- [ ] the no-escape fast path copies **nothing** — asserted by a test that parses a large scalar and measures the scratch's high-water mark at zero

### 0.1.5 — number scanning
- [ ] `NumInfo { kind, span, neg, base, big }` — classification, not materialisation (C-17)
- [ ] decimal, hex, octal and binary integer forms, and the decimal float form with exponent
- [ ] `big` set when the 64-bit accumulator would overflow, **and the literal still well-formed** — a 5000-digit integer is classified, not rejected
- [ ] `NPARSE_MAX_DIGITS` bounding the digit count before the value (C-16), so a megabyte of zeroes does not spend a megabyte of checked multiplies
- [ ] `-0` distinguishable: `neg` with a zero magnitude
- [ ] the accessors `num_int64`, `num_uint64`, `num_flt64`, `num_int256`, `num_text` — each total, each returning `Optional`

## Gate

**The worst-case program exits 0**, at -O0 and under `opt -O2`, having fed every
accumulation site in the module its adversarial input — and
`check_no_raw_accumulate` has been seen to fail against a planted violation.

That is PA-012 established as a fact rather than a claim, and every format cycle
after this one inherits it.

## Watch for

- **`end` and `in` are keywords**, and a cursor module wants both constantly.
  `hi` and `src` are the spellings (`specs/BUILD.md` §7).
- **The guard order in `scan_mul_add` is load-bearing.** `base == 0` must come
  before the division and `digit > bound` before the subtraction, or the helper
  traps in the function whose whole purpose is not trapping. The four `prove`
  comments are there so the order is documented as a proof rather than as a
  convention.
- **`opt -O2` matters here more than anywhere.** The guards are exactly the
  shape an optimiser might reorder, and B-3's re-run is what would catch it.
- **Do not materialise numbers.** The temptation to return an `int64` from the
  scanner is strong and PA-033 refuses it: the format decides, and the caller
  chooses the type.
