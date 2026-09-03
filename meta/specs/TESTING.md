# Testing

The instruments. The compiler project's recurring finding is that **the checks
that diff two lists found the holes and the tests did not**, and that a suite
which only ever agrees with what it is handed reports green while checking
nothing. This document is `nparse`'s answer to both.

---

## 1. The stages

`BUILD.md` §3 lists them; this is what each is *for*.

| Stage | Answers |
|---|---|
| `parse` | every source in the tree is readable by the real parser |
| `accept` | the public API compiles in a program that only imports it |
| `check` | every documented refusal actually refuses, with exactly its code |
| `program` | the library does what it says, judged by exit code, at -O0 and under `opt -O2` |
| `roundtrip` | parse → print → parse reaches a fixed point (`WRITER_MODEL.md` §4) |
| `corpus` | every case in a vendored conformance corpus is judged as the corpus says, and the pass count is **exact** |

---

## 2. Expectations

**Rule V-1.** Expectations live in the test file, as markers, and assert on
**codes and exit codes, never on message text** — the compiler's rule, adopted
whole, so that messages stay free to improve.

```
// expect-exit: 7
// expect-fault: DepthExceeded        the ParseError code this input must produce
// expect-fault-at: 12:5              and where
// expect-roundtrip: json             this case asserts a fixed point
// expect-error: NITPICK-TYPE-046     a compiler refusal, for the `check` stage
// stress: 40
```

**Rule V-2 — a negative test with no expectation is a failing test**, and
**unexpected diagnostics fail a test as surely as missing ones** (D-237): the
set of codes reported must **equal** the set the expectations name.

---

## 3. What the harness checks about the tree

Not tests. Checks that diff the library against the thing that describes it,
run on every full invocation, in the compiler's tradition where every one of
them found something on its first run.

| Check | Diffs |
|---|---|
| `check_no_raw_accumulate` | `src/scan/` and `src/format/` for a `*` or `+` on an accumulator outside `arith.npk` — **the no-trap rule, enforced** (`SCAN_MODEL.md` C-15) |
| `check_no_recursion` | every function in `src/` against a call-graph cycle — **the depth rule, enforced** (`SAFETY.md` §5). A cycle is a finding, and the exceptions table must name a reason |
| `check_no_owning_fields` | `Event`, `Node`, `ParseError`, `Frame` and every value stored in a `Vec` or an arena declare no owning field |
| `check_error_budget` | the count and names of public `error:` declarations against `SAFETY.md` §3's table — **two, and the check is what keeps it two** |
| `check_failsafe_arms` | the generated per-module arm list against a program that imports each module and compiles its `failsafe` |
| `check_layering` | every `use` edge against `BUILD.md` §6's diagram, including the `format` ↛ `doc` arrow specifically |
| `check_constants_named` | no bound outside `src/core/limits.npk` |
| `check_codes_documented` | every `FaultCode` variant appears in `DIAGNOSTIC_MODEL.md` §3's table and has at least one test that produces it |
| `check_corpus_provenance` | every corpus directory has a `PROVENANCE.md` naming its upstream commit, and the vendored tree's hash matches what it records |
| `check_specs_current` | reports, does not fail: spec sections whose cited symbols no longer resolve |

**Rule V-3 — `check_no_raw_accumulate` and `check_no_recursion` are the two
that matter most**, because they enforce the two rules that keep hostile input
from stopping a program (`SAFETY.md` §§4–5), and neither is a property a test
can establish. A test shows one input does not trap; the check shows the shape
that would is not present.

**Rule V-4 — `check_no_recursion` has an exceptions table and it must be
empty at 1.0.** Any entry needs a reason, and "this one is fine because the
depth is bounded by the grammar" is not one — a grammar does not bound what an
attacker sends.

---

## 4. The round-trip oracle

**Rule V-5 (PA-080) — the round trip is the test.**

```
   bytes from a corpus case
        │  parse
        ▼
   Document A ──── print ────► bytes' ──── parse ────► Document B
        │                                                  │
        └──────────────── doc_eq(A, B) ────────────────────┘
```

A reader that *accepts* a document and misunderstands it produces a plausible
tree, passes every "does it parse" case in the corpus, and shows up only here.
**This is the single most valuable instrument in the suite**, it costs a writer
the library wanted anyway (`WRITER_MODEL.md` §1), and it is why every format
cycle ships its writer in the same cycle as its reader.

**Rule V-6 — every corpus case that parses is a round-trip case** (W-12), so
the oracle's coverage is the corpus's coverage rather than a hand-written set.

**Rule V-7 — the second normalisation must be a fixed point.**
`print(parse(print(parse(b))))` equals `print(parse(b))` byte for byte. Testing
only `doc_eq` would miss a writer whose output parses to the same tree but
differs in bytes each time, which is a determinism failure the golden files
would otherwise catch late.

---

## 5. Conformance corpora

**Rule V-8 (PA-081) — the corpora are vendored and committed**, under
`tests/corpus/<name>/`, each with a `PROVENANCE.md` recording the upstream
repository, the commit hash, and the date it was taken.

*Reasoning.* A build must never fetch (the compiler's D-078: a build that needs
a network fails where safety-critical software is built). And a corpus that
changed underneath us would silently change what "conformant" means — the
number would still be green and it would mean something else.

**Rule V-9 — the expected pass count is exact, and an unexpected improvement
fails the run** (B-9). A count that went up usually means a case was
reclassified upstream or a fault was silently downgraded to acceptance, and both
want a human. Bumping the number is a deliberate commit.

**Rule V-10 — the `i_` cases get recorded verdicts, not pass/fail.**
JSONTestSuite's implementation-defined set is where the interesting divergences
live; `nparse` records its answer for each in a committed file, and a change to
any of them is a red run. That is the mechanism by which "we changed how a
number parses" becomes visible rather than discovered.

**Rule V-11 — a filtered corpus states its filter.** The yaml-test-suite runs
filtered to the shipped subset (`FORMATS.md` §4), and the filter is a committed
list of case identifiers with the excluded construct named per case — not a
regex, not a count. Every excluded case must produce `Fault(Unsupported)`, so
the exclusions are *tested*, not skipped.

---

## 6. Differential testing

**Rule V-12 (PA-082) — the tree and the stream must agree.** For every corpus
case, the event stream is captured directly and also reconstructed by walking
the `Document` the same case builds, and the two sequences must be identical.

This catches the class where the builder mishandles what the parser reported
correctly — a dropped member, a mis-parented value, an off-by-two in the
key/value alternation (`VALUE_MODEL.md` D-5). Neither the corpus nor the round
trip finds it reliably; the round trip can even hide it, because a symmetric
bug in the builder and the writer cancels.

**Rule V-13 — TOML's expected JSON is a third, independent oracle**
(`FORMATS.md` R-12, `WRITER_MODEL.md` W-13). It is worth naming separately
because it is the only check in the suite that does not go through our own
reader at all.

---

## 7. Fuzzing

**Rule V-14 (PA-083).** `tools/fuzz.py` drives every shipped `Format` with
random bytes and with structured mutations of the corpora, asserting:

1. **it never traps** — the process exits with the program's own code, never
   through `failsafe` with `IntOverflow`, `OutOfBounds` or `Unreachable`;
2. **it always terminates** — a step counter bounded at `4 × input length`;
3. **it consumes every byte exactly once** — span coverage sums to the input;
4. **allocation is bounded** — the scratch high-water mark stays under
   `NPARSE_MAX_SCALAR`;
5. **a parse that succeeds round-trips** — the oracle runs on every accepted
   fuzz input, which is where the interesting failures are.

**Rule V-15 — invariant 1 is the one that matters.** `SAFETY.md` §4's no-trap
rule is the library's central claim, and the fuzzer is the only thing that tests
it at scale. The corpus for it is seeded with the shapes designed to break it:
a 5000-digit integer, an exponent of `1e999999999`, fifty thousand `[`, a
100 MB string, a `\u` escape at every boundary.

**Rule V-16 — anything the fuzzer finds becomes a permanent case** in
`tests/fixtures/`, with the fault it produced recorded in the marker. A fuzzer
finding that is fixed and not kept is a fuzzer finding that comes back.

---

## 8. Performance

**Rule V-17.** `harness/bench.py` writes a line per benchmark into
`meta/bench/<date>.txt` and the harness fails on a regression worse than 20%
against the committed baseline, on the same machine. The benchmarks: a 100 MB
JSON parse to events; the same to a `Document`; a 10 MB TOML parse; a 100 MB
CSV parse; a document print; and the transcode loop (`WRITER_MODEL.md` W-15).

**Rule V-18 — bytes allocated is reported beside time**, because "nothing
proportional to the input is copied" (`SAFETY.md` §6) is a claim, and a claim
nobody measures is a claim nobody has. The event path's allocation must be
**constant** in the input size, and the benchmark asserts it.

---

## 9. The harness is tested

**Rule V-19 (the self-check).** `harness/selfcheck.py` feeds the harness wrong
expectations and requires it to report every one as a failure:

- a `program` case with the wrong `expect-exit`;
- a `check` case expecting a code the compiler does not report;
- a `check` case reporting a code no expectation names (the D-237 rule);
- a `roundtrip` case whose second parse differs;
- a `roundtrip` case whose *trees* match but whose second print differs
  byte-for-byte — the case that proves V-7 is doing work;
- a `corpus` entry whose pass count is one too low **and one too high**;
- a `check_no_raw_accumulate` violation planted in a scratch file;
- a `parse` case that does not parse.

**Rule V-20 — the self-check runs first in every full invocation.** A harness
that has not proven it can fail has not proven anything.
