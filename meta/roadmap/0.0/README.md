# Cycle 0.0 — Foundations

**The probes, the harness, and `src/core/`.** Nothing in this cycle parses anything. What it produces is the ability
to find out whether the rest of the plan is buildable, and the machinery every later cycle is tested by.

**Being re-derived at compiler `7e91730` (from 2026-10-15) by the Team seat's planners, as one pass over all six
subcycle files.** They were written execution-grade at the repository's setup (2026-09-03), against the compiler's
cycle 1.5 and LLVM 20.1.2; each is re-measured at the pin, with what the audits found owed carried into the step that
owes it. **The re-derivation lands subcycle by subcycle, in order**, and the table below says which files are at the
pin; a file not yet marked still holds its first writing — not to be executed as it stands — and the items it owes are
in the owed-items table below.

| File | At `7e91730` |
|---|---|
| [0.0.0](0.0.0.md) | **yes** — probes measured, five patches, blocks with filled Expects |
| [0.0.1](0.0.1.md) | **yes** — six patches over 0.0.0's record, blocks with filled Expects; CI's run is its worker's |
| [0.0.2](0.0.2.md) | **yes** — three patches over 0.0.1's record, blocks with filled Expects, the mutants' table; CI's run is its worker's |
| [0.0.3](0.0.3.md) | not yet |
| [0.0.4](0.0.4.md) | not yet |
| [0.0.5](0.0.5.md) | not yet |

## Why this shape

Two of the compiler project's most expensive lessons decide this cycle's contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4 was mostly repair, and every repair
  dated to the cycle that had parsed the construct. `nparse`'s design leans on language shapes that had never been
  exercised in this combination — the specification's `Event` in a `Vec`, an arena whose `get` copies POD nodes, a
  payload enum over two structs, a trait with a `Self->` receiver reached through a bound and through `dyn`. **0.0.0
  asks the compiler about all of them before anything is built on them** — and at `7e91730` it answered that the
  specification's sizes, summed from field widths, were wrong for `Event`, `ParseError` and `Node`; that several of
  its reasons named a mechanism the compiler does not use; and that the trait's static path is a compiler defect.
- **"Diagnostics come first, not last — they are how every later cycle is tested."** Here that is the harness. A
  suite written after the code is a suite shaped by the code.

**One probe is different from the rest and is the reason the cycle opens with them.** Probe 01 is not asking whether
a shape *compiles* — it demonstrates that the naive decimal accumulator **traps** on a long number and that the checked
helper **does not**. That is `PA-012`, the library's central correctness claim, established as a fact on day one
rather than asserted in a document. It is two programs, 01a and 01b, because a program that traps cannot also assert.

## Decisions in

PA-001 … PA-009, PA-012, PA-021, PA-022, PA-030. All settled. **Nothing in this cycle is blocked on a question.**

**And the ones this cycle proposes**, from PD-129 on, in the Team seat's block for this repository (PD-129 …
PD-148), each landing in the subcycle step that first needs it and numbered at the review (`tools/decisions.txt`,
which gains a line as each subcycle's file reaches the pin). Each is settled with a recommendation and states its reversal; **none is left open for the
author.**

| PD | Subcycle | Decides |
|---|---|---|
| PD-129 | 0.0.0 | the specification's types keep their enum fields, at their measured sizes |
| PD-130 | 0.0.0 | what an owning value may be stored in: the arena refuses at its make; a `Vec`'s free must drop its owners |
| PD-131 | 0.0.0 | static dispatch through a bound is held on a compiler defect, and nothing is re-spelled around it |
| PD-132 | 0.0.0 | every slot a reader's bytes reach is the read-only view; a view travels only as far as its bytes |
| PD-133 | 0.0.0 | native recursion traps; PA-022 stands, its reason a whole-program stop |
| PD-134 | 0.0.0 | what a consumer owes, measured; the tests' arm codes |
| PD-135 | 0.0.1 | the layering is a table of what each module imports |
| PD-136 | 0.0.1 | the toolchain is LLVM 20.1.8 with the compiler's target rows, in the manifest and in CI |
| PD-137 | 0.0.1 | one currency table; the library is security-sensitive, and its three research items gate cycle 0.1 |
| PD-138 | 0.0.2 | the build is one module per root, held to the target rows, scanned two ways on both legs, and reproducible from two directories |
| PD-139 | 0.0.2 | a unit red on a compiler defect is pending: its right answer, the one failure it is excused, and a reviewed list |
| PD-140 onward | 0.0.3 … 0.0.5 | proposed by those files as they reach the pin |

## The pin, and what each later landing would move

**Plan at `7e91730`** — the workbench's pin, landings 83 … 103 — and **re-pin once, at landing 118**, by the
author's word on the workbench's question 32 (2026-10-15 12:04), so that one adoption carries 104 … 118: the
use-after-free fix (116), the refusal of generic value parameters (117) and the two link fixes (118). If 118 has not
landed when the adoption round starts, the pin is the newest landing on the compiler's `main` then, never before 115,
and **a pin below 118 flips only what it carries**. *(Corrected 2026-10-15 by the pass's continuation: this said
"after landing 115", the author's word of 07:42, which question 32 superseded.)* The table names each place in this
cycle's plan a landing would move, so that **the adoption is this list, not a search**. A re-pin is taken **between subcycles**, never inside
one (the early ecosystem audit's EC9: the `7e91730` pin itself was taken mid-cycle elsewhere); a subcycle that has
started finishes at the pin it started at.

| Landing | What it does, by the compiler's notice or the board | What it would move here |
|---|---|---|
| 104 (DEF-249) | an `exit` operand is held to `int32`, `NITPICK-TYPE-007` otherwise | **nothing**: every `exit` operand the cycle's programs write is an `int32` — a literal, a `=>! int32` cast (the size probes' `#size_of`, an `int64`), an `int32` `Result`'s value, an `int32` call — counted by 0.0.0's §1.6 and re-counted by each later subcycle's facts |
| 105 (DEF-159) | a value stored through a held `@x` after `move(x)` is dropped at the scope's exit; the emission of every function with an address-taken owning binding moves | **no answer moves**: the cycle holds no `@` in a binding (§1.6). What moves is emission: the compiler's own `npkc.ll` digest, which 0.0.1's CI asserts against the pin's row, and any IR byte count a record quotes |
| 106 (D-342 R1, D-343) | an enum values every variant or none; a macro parameter the body declares is refused | **nothing**: no valued enum variant, no macro |
| 107 (DEF-243) | a builtin named as a value is refused | **nothing**: every builtin is called |
| 108 (DEF-202) | an aggregate `fixed` binding may be initialised by naming another | **newly allowed**, not used: every `fixed` table stays a literal (probe 12); probe 01b's `U64_MAX` is a scalar built from a scalar, which `7e91730` accepts |
| 109 (DEF-224, D-352) | `failsafe`'s `pick` is found through bare blocks | **newly allowed**, not used: every `failsafe` opens with its `pick` |
| 110 (DEF-226) | `pick (r.is_error)` carries the check out | **nothing**: the cycle tests a `Result` with `if (r.is_error)` |
| 111 (DEF-233, DEF-238) | a `give` or `fall` outside its arm is `NITPICK-TYPE-094`; a `frac` member written is `NITPICK-TYPE-024` | **nothing**: none written. At `7e91730` a stray `give`/`fall` ends `npkc` at exit 3 with no message, which a refusal fixture would misread; none is planned |
| 112 (DEF-232; its notice F54; on the compiler's `main` as `958890a`) | a `NIL` member is the zero-sized `{}`, as D-084 says; the checker unchanged | **nothing**: no `NIL` field (`tools/shapes.py`, in each subcycle's facts) |
| 113 (its notice F55: DEF-235, DEF-236 (c)(d)(e), DEF-237, DEF-234 (c)) | `NITPICK-PARSE-001` at a keyword declared as a name of ANY kind; `NITPICK-TYPE-045` at a `joins` deadline that is not a constant; `NITPICK-DERIVE-007` at an attribute not named `derive`, and at any attribute on a local binding (`DERIVE-004` at `#[derive]` on an impl); `NITPICK-RESOLVE-014` at an `opaque struct` outside an `extern` block; two texts | **nothing, checked against F55's text and the pin's keyword table**: every declared name of every kind the rule lists, in every `.npk` the cycle's patches add, read against `src/frontend/keywords.npk` at the pin — 170 words, the same set in landing 113's work — by `tools/names.py`, proved on a planted control holding each kind: none is a keyword. Every attribute is `derive`, on a struct or an enum; no `joins`, no `opaque`; and the two `??` the cycle writes, in probe 01b, are on an `Optional`, not a `Result`. *(Corrected 2026-10-15: this row named five words and a local `buffer`, the defects' first reading; F55's rule is every keyword, every kind of name.)* |
| 114 (DEF-250; F56) | the D-211 check hoisted out of the initialiser's branch: a module-level binding with no initialiser — `int64:counter;`, and the bare struct, `stack`, `wild`, `wildx`, `pub`, `atomic<int64>` and channel forms — is `NITPICK-TYPE-055` at its declaration | **nothing**: every module-level binding the cycle writes is a `fixed` one with an initialiser, but probe 12b's, a plain one with an initialiser, refused on purpose and `TYPE-055` at the pin already (`tools/rulings.py`) |
| 115 (DEF-251; F57) | every emitted `define` carries LLVM's `null_pointer_is_valid` | **every program's emitted IR moves, by design**: CI's `npkc.ll` row — the compiler's own emission, `b79f89c5…` at `7e91730` — moves with the re-pin as with any; the cycle records no digest or byte count of its own programs' IR, and no comparison of IR across two pins; and
0.0.0's §1.5 recursion edges, which measure the emitted frames at each leg, are re-measured by its block 0b. D-355, `NULL` legal only for `wild` pointers, is a later landing of its own: the cycle writes no `NULL` (`tools/rulings.py`) |
| 116 (DEF-252, the use-after-free) | a callee's store of a view into a place its caller owns asks DEF-42's holder-scope question at the call: `NITPICK-BORROW-002` | **probe 08h's verdict** (`tests/probe/defect/view_reseat/`): refused, its right answer — it flips at the adoption of a pin of 116 or later |
| 117 (D-353, with D-354) | a generic value parameter is a RESERVED form, refused by a code of its own, and D-336's corpus admits that verdict | **nothing**: none written; a capacity is a `fixed` constant (the libraries' S-135 answer) |
| 118 (DEF-253, with DEF-254) | a synchronous `Self->` method called through a generic bound links; and a trait's default method calling a sibling on `self`, which never linked, links | **probe 06's verdict** (`tests/probe/defect/bound_pointer_receiver/`): it links and runs, exit 0 — 0.0.2's PENDING unit on DEF-253, which flips at the adoption of a pin of 118, and not at a pin below it (the run then reddens to say its marker is stale, and the marker and its line in `harness/baseline/PENDING.txt` go); and nothing for DEF-254: no trait default calls a sibling on `self` (`tools/shapes.py`) |

**Also ruled in landing 112's commit** (D-353 … D-359, the board's notice F54), each held to what the cycle writes:
generic value parameters out until designed — 117 above; `NULL` legal only for `wild` pointers (D-355) — none written; a
payload-less enum variant as a constant outside the evaluator — no `fixed` initialiser names a variant; a `comptime func:`
compile-time only — no `comptime` written; the floor through `opt -O2` as its own measured landing — it moves the
runtime object, whose symbols 0.0.2's build step 1 re-measures on every run; and the orphan rule (S-37) — every `impl`
the cycle writes sits in the file that declares its type and its trait (`tools/rulings.py`). *(Corrected 2026-10-15:
this table said "nothing is known" of 114 and 115, and stopped there; the record's entries of 08:06, 08:08, 09:22 and
12:03 say what each is.)*

**Unbuilt and watched:** the compiler's D-341 (a `buffer` indexed and ranged, a view frozen like any other) is settled
and in no landing above; the day one carries it, 0.0.4's `Bytes` may offer a frozen view (its decision's reversal).

**At the re-pin, the adoption is:** 0.0.0's blocks 1 … 4 at the new pin (every verdict in its §6), the defect
directories' verdicts (re-derived first: the pin flips each fix it carries), each subcycle's facts block, CI's pinned rows (the commit and the compiler's `npkc.ll` digest,
`b79f89c5…` at `7e91730`), and this table's "what it would move" column, row by row.

## The shapes this cycle does not write

Open or silent at `7e91730`, from §2.2 of the workbench's planning brief for this cycle, of 2026-10-15 (A: the
answer differs between `7e91730` and later landings; B: open or silent at the pin; C: already in the pin), and the two
defects 0.0.0 found. Each subcycle's facts
block counts the lexical ones over what its patches add, with a scanner proved on planted and clean controls
(`tools/shapes.py`).

| Shape | How the cycle keeps clear of it |
|---|---|
| A1 an `exit` operand not exactly `int32` | every operand counted (landing 104's row) |
| A2 a `failsafe` `pick` below the body's top level | every `failsafe` opens with its `pick` |
| A3 an aggregate `fixed` binding naming another | tables are literals |
| A4 `pick (r.is_error)` then a read of `r.value` | `if (r.is_error)` |
| A5 `give` or `fall` outside an arm, or in a `defer` | none written |
| A6 a mixed enum, a macro parameter the body declares, a builtin as a value, a `frac` member write | none written |
| B7 a root imported back from a sibling directory (DEF-244) | no module imports a module that imports it; 0.0.3's `check_layering` holds it while DEF-244 is open |
| B8 a header failure reported two or three times (DEF-245) | a refusal fixture asserts the SET of codes (B-7), never a count of reports |
| B9 a `NIL` field (DEF-232) | none written |
| B10 `acquire`, `any`, `trit`, `nit`, a local `buffer` (DEF-235) | none written |
| B11 a `comptime` value parameter, a non-constant `joins`, an unknown attribute, a module-level `opaque struct` (DEF-236) | none written; attribute names counted |
| B12 `??` over a `Result` (DEF-237's advice) | `?!` and `?\|` only |
| B13 `use mod.f;` (DEF-234 (b)) | path forms only: `use "./x.npk".f;` |
| B14 a `buffer` read or written through an untied view (D-341 unbuilt) | `.ptr` behind the library's own checked accessors; no `#wild_slice`; no returned view |
| B15 wide strings | not spelled |
| B16 compiler documents its own tree contradicts (DEF-239), S-134 | the probes measure; no plan line rests on a reference sentence alone |
| C — `fixed T[]` and `string_bytes`; `TYPE-072` on a clause-less `while`; the six-arm floor; the generic by-value refusals; the symbol scan's blindness to a syscall | 0.0.0's PD-132; every `while` states `decreases`; every program names the floor (0.0.0 §1.4); `Vec<T: Copy>` (0.0.4); a call-edge scan (0.0.2) |
| a synchronous `Self->` method through a generic bound (0.0.0's first defect) | not written outside its defect directory (PD-131) |
| a view re-seated by a callee into a place it was handed (0.0.0's second defect) | not written outside its defect directory (PD-132) |
| a trait's default method calling a sibling on `self` (DEF-254, which links only from 118) | none written: `tools/shapes.py` counts it, with its own planted control (0.0.2 on) |
| a module-level binding with no initialiser, or a plain one (DEF-250 at 114; D-211) | every one `fixed` with an initialiser but probe 12b's, refused on purpose: `tools/rulings.py` (0.0.2 on) |

And `PLAYBOOK.md` §2's rows open at the pin are kept: the read-only view; no part of a `fixed` binding written; every
path leaving explicitly; `main` exactly `int32(cstring[]:_~argv)`; each `Result` tested alone; a qualified `pick` arm;
no literal outside the envelope; `#size_of` measured, never summed; a container's free drops its owners.

## What the audits found owed, and where each is carried

| Item | Carried by | How |
|---|---|---|
| PL-1, the read-only view (E2-2) | 0.0.0 step 4 | every reader, cursor, text and document slot `fixed uint8[]`, measured by probe 08's family; PD-132 |
| PL-2, the writer's sink and `Bytes.view()` | 0.0.0 step 4; 0.0.4 | `put`'s `text` is `fixed` (PD-132); `Bytes` has no returned view at the pin |
| PL-3, the probes the view needs | 0.0.0 steps 2 … 4 | probes 08 … 08h, 12's range, 08f's `TYPE-014` |
| PL-4 and E2-4, LLVM 20.1.8 and the manifest's rows | 0.0.1 | `[toolchain]` with `llvm`, `triple` and `datalayout` as the compiler's `BUILD_REFERENCE.md` §1 gives them, worded as `nitpick-regex`'s manifest; `CLAUDE.md` and `README.md`; CI |
| PL-5, the compiler's state | 0.0.0 step 4 | `BUILD.md` §1 re-read and dated, `README.md`'s status, O-N2 answered, PA-022's note |
| PL-6, `=> dyn` and landing 94 | 0.0.0 step 3 | probe 07 drives an owning implementation through the explicit cast |
| E2-6, where the dogfood consumer lives | 0.0.5 | the roadmap's four lines made PA-103's; which harness runs it |
| E2-10, counts against sets | 0.0.5 | `ROADMAP.md`'s decision and question counts derived from their sets; the workbench's `LIBRARIES.md` is the orchestrator's |
| E2-13, no `CURRENCY.md` | 0.0.1 | `meta/research/CURRENCY.md` created; the library counted security-sensitive and its three research items named |
| E2-15, `CLAUDE.md`'s empty heading | 0.0.1 step 5 | the paragraph moved under "What this is" |
| EC2, what an index does | 0.0.0 step 4; 0.0.4 | `SAFETY.md`'s row and `VERIFICATION.md` §2 with probe 11's measurement; the accessors guard every pointer index |
| EC3, "every public `error:`" | 0.0.3 | `check_error_budget` keyed by module and name, private identities included, and the sentences and their twins |
| ED2, local `O-N` ids | 0.0.0 steps 2 and 4 | O-N2, O-N3 and O-N4 each say their id is this repository's own; nothing takes a registry id |
| ES1, "nothing exists today" | 0.0.0 step 4 | O-N2 struck as answered |
| EK1, `VERIFICATION.md` P-1 | 0.0.4 | P-1 replaced: an obligation is a comment unless a decision accepts the arm its live clause costs |
| EC9, a re-pin mid-cycle | this README | a re-pin is taken between subcycles; the landing table is the adoption |

## The planning brief's open points, and each one's answer

| # | Point | Answer |
|---|---|---|
| 1 | which compiler the plan targets | `7e91730`; the landing table above |
| 2 | probe 05's meaning | settled by 0.0.0: refused at `arena_make`, `NITPICK-TYPE-007` (PD-130) |
| 3 | returned reader structs | settled by 0.0.0: a constructor returns its cursor over the bytes it was handed; over its own, `BORROW-001` (PD-132) |
| 4 | `Bytes` and D-341 | settled by 0.0.0's probe 11 — a `buffer` can be neither indexed nor ranged at the pin — and handed to 0.0.4 |
| 5 | `#size_of<Event>()` and an enum's width | settled by 0.0.0: four bytes; `Event` 32 (PD-129) |
| 6 | probe 10 against the 8 MiB stack | settled by 0.0.0: 50 000 levels complete; the traps are at 65 535 and 131 063 (PD-133) |
| 7 | the bill, and `IntOverflow` | settled by 0.0.0's oracle measurements (PD-134) |
| 8 | whether `nitpick-regex`'s answer on live contracts (A′, its `VERIFICATION.md` P-1b) binds this library | handed to 0.0.4, which writes the obligations (EK1) |
| 9 | the `repro` check | settled by 0.0.2: each copy carries its manifest, since without it the consumer's two modules differ — the check's mutant (PD-138, `BUILD.md` B-4) |
| 10 | the undefined-symbol scan | settled by 0.0.2: the call-edge scan stands behind PA-006, over every module under `src/` and every program, and the floor and the syscaller are its controls on every run (PD-138, B-2a) |
| 11 | `tools/parse_check` and `tools/check` | handed to 0.0.3: `npkc` and the code family; `accept` struck |
| 12 | which harness runs the dogfood consumer | handed to 0.0.5 (E2-6) |
| 13 | the currency file's name | handed to 0.0.1 (E2-13) |
| 14 | sweeps | settled: every sweep runs inside this repository and prints its denominator (`tools/sweep.py`) |

## The three places the first writing disagreed with itself

- **Probe 01 is two programs**, 01a and 01b: one traps, so it cannot also assert. The checklist below names both.
- **`check_no_owning_fields` goes live at cycle 0.2**, as `0.0.3.md`'s table has it, not at 0.0.3: the types it names
  do not exist until 0.2, and the containers' half is the compiler's from 0.0.4 on (`Vec<T: Copy>`).
- **A program links as one object and `npkrt.o`**, as the last line of `specs/BUILD.md` §2's drawing has it — while
  that drawing's `llc → build/nparse.o` line, and 0.0.2's own pipeline, draw a library object beside it. `npkc`
  compiles a program and everything it imports into one module, so there is no library object to link. 0.0.2
  measured it — an imported module's function is defined in the root's emission — and amends both (PD-138).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — the specification's shapes asked of the compiler at the pin, the flagship among them | a verdict per probe, the specifications amended by them, two compiler defects raised |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's toolchain rows and test table, CI, `CURRENCY.md` | `npkc` compiles an empty library and a program that imports it |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build, the `program` stage, the toolchain pin, `repro` | one test program builds, links, runs, and its exit code is judged |
| [0.0.3](0.0.3.md) | **The harness, part 2** — the refusal and parse stages, the self-check, the tree checks | the self-check proves the harness can fail |
| [0.0.4](0.0.4.md) | **`src/core/`** — `limits.npk`, `Vec<T>`, `Bytes`, `SmallMap<K,V>` | the primitives, with their suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

The 0.0.2 … 0.0.5 items are the re-derivation's targets, drawn from the audits' owed items and 0.0.0's verdicts; each
file states its own acceptance when it reaches the pin, and where the two differ, the file at the pin governs.

### 0.0.0 — the probes
- [ ] `tests/probe/probe01a_naive_accumulate.npk` traps `IntOverflow` (93) and `probe01b_checked_accumulate.npk` exits 0 — **the flagship**
- [ ] `probe02_pod_event.npk`, `probe03_payload_enum.npk`, `probe04_arena_pod.npk` — the specification's `Event`, `Step` and `Node`, each probe's exit code its size: 32, 36, 64
- [ ] `refused/probe05_arena_owning.npk` — refused at the make, `NITPICK-TYPE-007`
- [ ] `probe07_trait_dyn.npk` — the `Format` shape through `dyn`; and `defect/bound_pointer_receiver/` — the same through a bound, a compiler defect
- [ ] `probe08_view_edges.npk`, its six refusals, and `defect/view_reseat/` — the read-only view at every edge a reader uses
- [ ] `probe09_generic_move.npk` and the capped pair `probe09b`/`probe09c` — owners in a generic `Vec`, and the free that must drop them
- [ ] `probe10_explicit_stack.npk` exits 0 at 50 000 levels; `probe10b_native_recursion_traps.npk` traps `StackExhausted` (106)
- [ ] `probe11_bytes_growth.npk` — a million appends, twenty reallocations
- [ ] `probe12_module_fixed.npk` and its three refusals — a `fixed` table read and ranged; a plain module binding `NITPICK-TYPE-055`
- [ ] every verdict in `0.0.0.md` §6 re-measured, SAME, and every consequence in `meta/specs/` and `meta/DECISIONS.md` in the commit of its verdict
- [ ] `tests/probe/README.md`; block 6's sweep read

### 0.0.1 — the skeleton
- [ ] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list)
- [ ] every `src/` subdirectory has a placeholder module that compiles, so the parse sweep has something to sweep
- [ ] `nitpick.toml`'s `[toolchain]` pinned to LLVM 20.1.8 with the `triple` and `datalayout` rows, and its `[[test]]` table's first entries
- [ ] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles, links, runs and exits 0, with a comment naming O-N1
- [ ] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.8 and the compiler built from the pinned commit, every hex value quoted
- [ ] `meta/research/CURRENCY.md`
- [ ] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended

### 0.0.2 — the harness, part 1
- [ ] `harness/run.py`, `manifest.py`, `toolchain.py`, `expect.py`, `build.py`, `irscan.py`, `elf.py`, `stages.py`, and `baseline/`
- [ ] one program object and `npkrt.o` per link, every argv built from the manifest's flag lists, every module the manifest's target rows
- [ ] the undefined-symbol scan and the call-edge scan as build steps, over every module under `src/` and every program, the floor and the syscaller their controls on every run
- [ ] the `program` stage at -O0 and again under `opt -O2`, same exit required; `expect-exit`, `stress` and `mem-cap-mib` honoured
- [ ] the `repro` check: two builds from different working directories, each copy with its manifest — and **seen to fail** without it
- [ ] 0.0.0's `tests/probe/` green as the first real `program` suite; probe 06 PENDING on DEF-253, listed, and every way the mechanism can be wrong seen red
- [ ] CI's harness step asserting the runner's unqualified green summary

### 0.0.3 — the harness, part 2
- [ ] the parse sweep (`npkc` over every `.npk`, judged by the diagnostic's code family) and the refusal stage with the **exact-code** rule (B-7); `accept` struck
- [ ] 0.0.0's `refused/` judged by its codes, and `defect/`'s verdicts re-derived on every run
- [ ] `--only`, and output that says twice that a filtered run concludes nothing
- [ ] `harness/selfcheck.py`, its live cases each **seen red** and its pending ones printed as pending; it runs **first**
- [ ] `check_layering`, `check_error_budget` (keyed by module and name), `check_constants_named`, `check_no_raw_accumulate`, `check_no_recursion` live; `check_no_owning_fields` from 0.2

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — every constant from `specs/SAFETY.md` §7, each with the rule that set it
- [ ] `src/core/vec.npk` — `Vec<T: Copy>`, every accessor boundary-tested at `0`, `count-1` and `count`
- [ ] `src/core/bytes.npk` — `Bytes` over `buffer`, `put_uint` allocation-free, growth amortised linear and measured
- [ ] `src/core/smallmap.npk` — fixed-capacity, ordered, `EParseState` on overflow
- [ ] every accessor's obligation written as a comment in the syntax it will take, with a test standing in
- [ ] every suite program exits 0, so a leak of a `wild` block is a trap, and the managed half gated by a capped pair

### 0.0.5 — close
- [ ] every probe verdict reconciled against the specifications by **reading them**, not by remembering
- [ ] the cycle's findings written as a numbered list
- [ ] the close audit run and triaged (W-22); a full green run, verdicts committed
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes
- [ ] cycle moved to `done/0.0/`, `ROADMAP.md` updated

## Gate

**The cycle is complete when**: probe 01 has demonstrated the trap and its absence; a full `harness/run.py` is green;
the self-check proves the harness fails in every live way it names and reports the pending ones as pending;
`src/core/`'s three containers each have a suite; and every probe has a recorded verdict with its consequences
written into the specifications.

## Watch for

- **Probe 05 is expected to be refused, probe 01a and probe 10b to trap, and probe 06 and probe 08h to show a
  compiler defect** — from 0.0.2 on, probe 06 a PENDING unit stating its right answer. All are *results*. A subcycle fails only on a verdict that is **undecided** — a compiler crash, a
  hang, or output nobody can read — or one that differs from its plan's Expect.
- **A probe that fails is a finding, not an obstacle.** Record the exact diagnostic, decide the design change, amend
  the specification, and only then continue. Working around a compiler refusal in library code is what the compiler's
  own R6 forbids.
- **The reserved words will bite in `src/core/` specifically**: `end`, `in`, `limit`, `any`, `buffer`, `raw`, `move`
  and `stack` are all words a container library reaches for. `specs/BUILD.md` §7 has the substitutes — use `hi`,
  `src`, `bound`, `frames`.
- **`Vec<T>`'s block is `wild` storage** and every path out of a function that took some must release it, or `exit 0`
  traps under D-151 — a gate on the `wild` half only. A managed body is invisible to it (probes 09b and 09c).
