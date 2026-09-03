# Roadmap — the cycle map

The specification set (`meta/specs/`) is written and the decisions it rests on
are in `meta/DECISIONS.md`. This is the plan built on them.

**One decision batch is settled** — PA-001 … PA-083, written with the
specification set. What remains open in `../OPEN_QUESTIONS.md` is open *by
design*: five measurements taken in the cycles that can take them, two questions
waiting for a consumer to ask, one gated on the compiler's tooling, four that
are the compiler's rather than ours, and four for the project's author, none of
which gates cycle 0.0. **No cycle in this plan is blocked on a decision.**

## How this is organised

- **A cycle is a folder** — `0.0/`, `0.1/`, … — focused on **one topic**.
- **A subcycle is a file inside it** — `0.0.0.md`, `0.0.1.md`, … — one workable
  chunk of that topic, written execution-grade before its code is touched.
- **A finished cycle moves to `done/`**, so the active work stays easy to find.
- **Commit after every subcycle. Push at the end of every cycle.**
- **Every cycle's README carries a checklist.** Tick items as they land; the
  checklist is the cycle's state, and a cycle whose checklist is complete is a
  cycle ready to close.
- **Each cycle's opening subcycle file is written at the *previous* cycle's
  close**, by the session that just learned what that cycle taught. Cycle 0.0 is
  the exception, written up front because there is no previous cycle.

This convention is the compiler repository's, deliberately, so that a session
moving between the two reads one thing.

---

## The two constraints that shape everything

**A parser in this language has one central hazard, and it wears two hats.**

> **Plain integer overflow traps** (D-210), so `acc = acc * 10 + d` is a remote
> denial of service on a twenty-three digit number. **There is no stack-depth
> guard** (O-N2), so `[[[[[…` is an uncontrolled fault.

Both are *input* causing a *program stop*, which is the one thing this
ecosystem exists to prevent. PA-012 and PA-022 are the answers — checked
arithmetic through three helpers, and explicit stacks everywhere — and
`check_no_raw_accumulate` and `check_no_recursion` are what keep them true
(`specs/TESTING.md` §3). **Every cycle from 0.1 onward is judged partly on
whether it kept them.**

The second constraint is what shapes the *interface*:

> **Every public `error:` costs every consumer a `failsafe` arm** (REACH-002),
> and **there are no closures** (D-018).

The first made a syntax error a **value** rather than an error (PA-008), which
is this library's headline design decision. The second made the parser **pull**
rather than push (PA-020).

And one that shapes the *tooling*: **`npkg` cannot build a library** and
cross-repository imports do not resolve (O-N1), so `harness/` is the runner and
every import is relative. That is the first thing cycle 0.0 builds, because
everything after it is tested by it.

---

## Phase 0 — the library, built bottom-up

Nothing here is user-facing until 0.3. Each cycle is testable on its own, and
because the library makes **no syscall at all** (PA-006) there is no device to
stand in for: every cycle's suite is bytes in and values out.

| Cycle | Topic | Gated on |
|---|---|---|
| **0.0** | **Foundations** — the language probes, the harness, `src/core/` | — |
| **0.1** | **Scan** — the cursor, spans, UTF-8, escapes, and the arithmetic that cannot trap | 0.0 |
| **0.2** | **The event contract** — `Event`, `Step`, `ParseError`, the `Format` trait, the depth stack, `event_validate` | 0.1 |
| **0.3** | **JSON** — the first plugin end to end, the conformance harness, and the trivial fifth format | 0.2 |
| **0.4** | **The document** — the arena tree, the pool, ordered maps, duplicates, the accessors, paths | 0.3 |
| **0.5** | **The writers and the oracle** — the canonical JSON writer, the `roundtrip` stage, differential testing | 0.4 |
| **0.6** | **TOML** — reader and writer; toml-test and its expected-JSON second oracle | 0.5 |
| **0.7** | **CSV** — reader and writer; the dialect surface | 0.5 |
| **0.8** | **YAML** — the stated subset, reader and writer | 0.5 |
| **0.9** | **Diagnostics and recovery** — rendering, `expected` sets, resynchronisation, multi-fault collection | 0.6, 0.7, 0.8 |
| **0.10** | **Streaming and large inputs** — the 1 GB measurement, JSON Lines, constant-allocation proof | 0.5 |
| **0.11** | **Performance** — the benchmark suite, the committed baselines, the regression gate | 0.10 |
| **0.12** | **The dogfood consumer** — a configuration linter, written against the library as a user | 0.9, 0.11 |
| **0.13** | **Hardening** — the fuzz sweep, the corpora completed, the verification obligations reconciled | 0.12 |
| **1.0** | **Release** — documentation, the API freeze, the `failsafe` arm contract, versioning | 0.13 |

---

## What each cycle produces

Enough detail that a reader can tell whether a cycle is finished without
opening it. The per-cycle README has the subcycle map and the checklist.

### 0.0 — Foundations
The **language probes** first: twelve small programs asking the compiler whether
the shapes the design depends on are spellable — a 24-byte POD in a `Vec`, a
tagged enum with payloads in a `pick`, an arena of POD nodes with a `get` that
copies, a trait with a `Self->` receiver through a bound **and** through `dyn`,
a `uint8[]` borrow at every escape-analysis edge, and — the one that matters
most — **an accumulate-with-check that provably does not trap where the naive
one does.** A probe that fails changes the design.

Then the harness (`harness/run.py`, its self-check, the stages), the manifest's
test table, CI, and `src/core/` — `Vec<T>`, `Bytes`, `SmallMap<K,V>` and
`limits.npk`.

### 0.1 — Scan
`src/scan/`: the total cursor, `Span`, the generated 256-byte class table, the
UTF-8 decoder, the escape primitives, and **`arith.npk`** — the three checked
helpers that are the only place in the library an input-derived value is
multiplied or added.

**The cycle's own gate:** a program that feeds every accumulation site its
worst case — a 5000-digit integer, `1e999999999`, a `\u` escape at every
boundary — and **exits 0**, proving no path traps. Plus `check_no_raw_accumulate`
live and *seen to fail* against a planted violation.

### 0.2 — The event contract
`src/event/` and `src/diag/`: `Event` (24 bytes, POD, asserted), `Step`,
`ParseError` (24 bytes, POD, asserted), `TextRef`, `Options`, the `Format`
trait, the preallocated depth stack, and **`event_validate`** — the wrapper
`Format` that asserts the stream grammar and is what every plugin is developed
against.

**The cycle's own gate:** `event_validate` catches each of the six grammar
violations in `specs/EVENT_MODEL.md` §3, proven by a deliberately broken test
format.

### 0.3 — JSON
`src/format/json.npk`: RFC 8259 complete, plus `json_lines_reader`. And the two
things that make it more than one format: **`plugin_conform`**, the harness that
mechanically checks `specs/PLUGIN_MODEL.md` §3's eight obligations, and the
**trivial fifth format** in `tests/` that proves nothing in the library knows
the shipped formats are special.

**The cycle's own gate:** JSONTestSuite vendored, every `y_` accepted, every
`n_` faulted, every `i_` verdict recorded — and `plugin_conform` green over both
JSON and the trivial format.

### 0.4 — The document
`src/doc/`: the arena of POD nodes, the pool, the sibling chain, insertion order,
the duplicate policy, `doc_index`, the six numeric accessors including
`doc_int256`, `doc_eq`, the path language, and the explicit-stack build, walk,
compare and drop.

**The cycle's own gate:** the differential test — for every JSONTestSuite case,
the event stream captured directly equals the stream reconstructed by walking
the document built from it.

### 0.5 — The writers and the oracle
`src/emit/json.npk`, the `EventSink` trait, the `roundtrip` harness stage,
`--record-golden`, and the self-check cases that prove a tree mismatch **and** a
byte mismatch both fail.

**The cycle's own gate:** the round trip green over the whole `y_` corpus, and
the second print byte-identical to the first (`specs/TESTING.md` V-7).

### 0.6–0.8 — TOML, CSV, YAML
Three cycles because the formats have different hard parts: TOML's table-header
semantics, CSV's dialect surface and total absence of a specification, YAML's
indentation and the subset boundary. Each ships **reader and writer together**
(PA-060) and each is gated on its corpus. TOML additionally gets the
expected-JSON second oracle, which is the only check in the suite that does not
go through our own reader.

### 0.9 — Diagnostics and recovery
`fault_render` with the caret line, the `expected` masks filled in per format,
per-format resynchronisation, multi-fault collection, and O-P3/O-P10's shared
measurement.

### 0.10 — Streaming and large inputs
The 1 GB measurement that turns `specs/EVENT_MODEL.md` E-25 from a claim into a
number: parse a 1 GB JSON document through the event path and **assert the
allocation is constant in the input size**. Plus JSON Lines proven, and O-P6
answered with the measurement rather than a guess.

### 0.11 — Performance
`harness/bench.py`, the six benchmarks, the committed baselines, the 20%
regression gate, and **bytes allocated reported beside time** — because "nothing
proportional to the input is copied" is a claim and a claim nobody measures is a
claim nobody has. O-P8's interning measurement lands here.

### 0.12 — The dogfood consumer
A configuration linter in `examples/`, reading TOML, JSON and YAML, using
`Document`, recovery, multi-fault rendering and the path language — the four
things nothing else in the plan exercises hard. Written **without changing the
library**, so every friction is recorded rather than smoothed over, then
triaged: defect, gap, or accepted cost.

### 0.13 — Hardening
The fuzz corpus swept to exhaustion against all five invariants, the corpora
completed and their pass counts pinned, `check_no_recursion`'s exceptions table
proven empty, and `specs/VERIFICATION.md`'s obligation list reconciled against
what the code actually generates and handed forward as `meta/OBLIGATIONS.md`.

### 1.0 — Release
`docs/` written, the public API frozen and enumerated in `src/lib.npk`, the
`failsafe` arm contract published per module, an example per format plus the
transcode loop and a custom plugin, and PA-009's version policy stated where a
consumer will read it.

---

## Post-1.0, as a map rather than a plan

| Cycle | Topic |
|---|---|
| **1.1** | **Full YAML** — anchors and aliases with an expansion budget as a first-class part of the design, merge keys, tags, directives, multi-document (Q-1) |
| **1.2** | **XML** — opening with a decision batch whose first item is the event-vocabulary extension `Attribute` and mixed content requires (Q-2, PA-025) |
| **1.3** | **The CST question** — whether `nitpick-cst` should exist and use `src/scan/` (PA-007) |
| **1.4** | **Verified build** — `nparse`'s obligations through the compiler's `npkg verify`, once that reaches libraries |

---

## Ordering notes

- **The probes come first, in 0.0, not last.** The compiler's own experience is
  the argument: *a construct that parses is not a construct that works*, and
  three of its cycles were mostly repair to constructs an earlier cycle had
  "finished". The probe that matters most here is the checked accumulate, and it
  is a *positive* result we need rather than a refusal — a demonstration that a
  hostile numeric literal exits 0 where the naive version traps.
- **The harness comes first too**, for the compiler's stated reason about
  diagnostics: it is how every later cycle is tested, and a suite written after
  the code is a suite shaped by the code.
- **The scanner precedes every format**, which is the whole premise of the
  library: what the prototype's five parsers each rewrote was not the grammar,
  it was this.
- **JSON is first among the formats** because it is the smallest complete
  specification with the best corpus, so the *path* — scanner to events to
  conformance harness to corpus — is proven on the format least likely to
  confuse a path problem with a format problem.
- **The document follows a format rather than preceding one**, because a value
  model designed before anything produced values is a value model designed
  against imagination. JSON's corpus is what tells us whether the node layout
  works.
- **The oracle precedes TOML, CSV and YAML.** Writing the round trip at 0.5
  means the three harder formats are developed against an instrument that
  already works, rather than each being judged by "does the corpus pass".
- **Recovery is late, at 0.9**, because it needs every format's
  resynchronisation rule to exist before the shared machinery can be right, and
  because it is the one feature the linter (0.12) will genuinely exercise.
- **Verification obligations are written from cycle 0.0 onward**, in the syntax
  they will take, enforced by property tests until the compiler's 1.5 makes them
  real. The compiler's R9 is explicit: obligations discovered in a branch and
  never collected are the cheapest way to lose the campaign.
- **A decision precedes the cycle that needs it.** Each cycle's README lists its
  open questions; a cycle whose questions are open is not ready to start.

---

## What to expect, from the compiler's experience

Four findings the compiler project paid for, in this library's terms.

**A construct that parses is not a construct that works.** Here: a format that
accepts a corpus is not a format that *understands* it, and the round-trip
oracle at 0.5 is the analogue of the sweep that found those. It is why the
writer ships with the reader rather than after.

**An analysis right on straight-line code and wrong after a merge passes every
test written the easy way.** Here: a parser right on well-formed input and wrong
on a truncated one, and a scanner right on a short number and wrong on a long
one. Both have a dedicated test shape — the fuzzer, and 0.1's worst-case gate —
because neither is found by testing the easy way.

**Every hole was found by a check that diffs two lists, and none by a test.**
`specs/TESTING.md` §3 is this library's list, and the two that matter —
`check_no_raw_accumulate` and `check_no_recursion` — enforce properties **no
test can establish**: a test shows one input does not trap, the check shows the
shape that would is not present.

**A suite that only ever agrees with what it is handed is worse than no suite.**
The harness self-check (V-19) is not optional and runs first, and it includes a
corpus count that is one too *high* as well as one too low.

---

## The cycle-numbering convention

Cycle numbers sort lexically only up to `0.9`; `0.10` sorts before `0.2` in a
plain listing. The compiler hit this and chose correctness over comfort, and so
does this plan: **the table above is authoritative over lexical order.**
Renumbering to keep single digits would invalidate every cross-reference the
moment a cycle is inserted, which is a cost this project has watched the
compiler pay twice.
