# Cycle 0.0 — Foundations

**The probes, the harness, and `src/core/`.** Nothing in this cycle parses anything. What it produces is the ability
to find out whether the rest of the plan is buildable, and the machinery every later cycle is tested by.

**Re-derived at compiler `7e91730` (2026-10-15) by the Team seat's planners, T6 and its continuation T6b, as one pass
over all six subcycle files.** They were written execution-grade at the repository's setup (2026-09-03), against the
compiler's cycle 1.5 and LLVM 20.1.2; each is re-measured at the pin, with what the audits found owed carried into the
step that owes it (the owed-items table below). **All six are at the pin**, each rehearsed over a simulated record of
the subcycles before it, and the pass's last commit ran every block of all six once more, each `SAME`. **Its first fix
round** (2026-10-15, after the plan verification's FAIL) answered that verification's findings at their source — the
tools, the six files' patches and texts, and this README — and moved the research gate to cycle 0.0's first dispatch
(PD-137, by the libraries' reviewer's ruling); its own confirmation pass ran every block of all six again. **Its
research re-cut** (2026-10-16), after that gate fired on the three digests, held their findings — `CURRENCY.md`'s
research section, in 0.0.1's step 5, says where each is held, or who decides it — and 0.0.0's gate item 7 now knows
the three by their sha256. **Its adoption of the libraries' first re-pin** (2026-10-16) moved it to compiler `c9baa9e`
before any subcycle started, by the landing table below, row by row. **The second re-pin**, to compiler `2e1cb4a` at
landing 140, came after 0.0.0 and 0.0.1 had run at `c9baa9e`: its adoption is the lettered subcycle
[0.0.1a](0.0.1a.md) (the workbench's rule W-31), planned on 2026-10-23 (T12) with 0.0.2 … 0.0.5 re-derived at the new
pin, by the table's rows 119 … 140, each measured.

| File | At `2e1cb4a` |
|---|---|
| [0.0.0](0.0.0.md) | **done at `c9baa9e`** — its record; its probes' verdicts measured again at `2e1cb4a` by 0.0.1a's old-pin leg |
| [0.0.1](0.0.1.md) | **done at `c9baa9e`** — its record; its CI moves to `2e1cb4a` by 0.0.1a's step 1 |
| [0.0.1a](0.0.1a.md) | **yes** — the adoption: two patches over 0.0.1's record, the old-pin leg and the sweep, blocks with filled Expects; cut into fresh-worker steps, each pushed and its CI run read |
| [0.0.2](0.0.2.md) | **yes** — four patches over 0.0.1a's record, the fourth carrying out ten of cycle 0.0.1's twelve items as ruled; blocks with filled Expects, the mutants' table; cut into fresh-worker steps, each pushed and its CI run read |
| [0.0.3](0.0.3.md) | **yes** — three patches over 0.0.2's record, blocks with filled Expects, the mutants' table; CI's run is its worker's |
| [0.0.4](0.0.4.md) | **yes** — four patches over 0.0.3's record, blocks with filled Expects, the mutants' table; CI's run is its worker's |
| [0.0.5](0.0.5.md) | **yes** — two patches over 0.0.4's record, blocks with filled Expects, the archive its last block; its execution, the close, is the libraries' seat's |

## Why this shape

Two of the compiler project's most expensive lessons decide this cycle's contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4 was mostly repair, and every repair
  dated to the cycle that had parsed the construct. `nparse`'s design leans on language shapes that had never been
  exercised in this combination — the specification's `Event` in a `Vec`, an arena whose `get` copies POD nodes, a
  payload enum over two structs, a trait with a `Self->` receiver reached through a bound and through `dyn`. **0.0.0
  asks the compiler about all of them before anything is built on them** — and at `7e91730` it answered that the
  specification's sizes, summed from field widths, were wrong for `Event`, `ParseError` and `Node`; that several of
  its reasons named a mechanism the compiler does not use; and that the trait's static path was a compiler defect —
  which the compiler fixed in its landing 118, so at the pins `c9baa9e` and `2e1cb4a` the answer is that it runs.
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
| PD-131 | 0.0.0 | static dispatch through a bound is the intended path, measured; nothing was re-spelled around the defect that held it |
| PD-132 | 0.0.0 | every slot a reader's bytes reach is the read-only view; a view travels only as far as its bytes |
| PD-133 | 0.0.0 | native recursion traps; PA-022 stands, its reason a whole-program stop |
| PD-134 | 0.0.0 | what a consumer owes, measured; the tests' arm codes |
| PD-135 | 0.0.1 | the layering is a table of what each module imports |
| PD-136 | 0.0.1 | the toolchain is LLVM 20.1.8 with the compiler's target rows, in the manifest and in CI |
| PD-137 | 0.0.1 | one currency table; the library is security-sensitive, and its three research items gate cycle 0.0's work, answered at its first dispatch (0.0.0's gate) |
| PD-138 | 0.0.2 | the build is one module per root, held to the target rows, scanned two ways on both legs, and reproducible from two directories |
| PD-139 | 0.0.2 | a unit red on a compiler defect is pending: its right answer, the one failure it is excused, and a reviewed list |
| PD-140 | 0.0.3 | the refusals and the sweep are judged by `npkc`; `accept` struck; a refusal a set of codes at their sites; a refusal the pin does not give a pending one |
| PD-141 | 0.0.3 | the self-check is its own printed list, live and pending, run before any judgment; a filtered run concludes nothing |
| PD-142 | 0.0.3 | the tree checks read their authorities; the error budget keyed by module and name, private identities included |
| PD-143 | 0.0.4 | `limits.npk` holds `SAFETY.md` §7's eight bounds at 0.0.4, and `VALUE_MODEL.md` D-16's ninth joins them with its switch, in cycle 0.4 |
| PD-144 | 0.0.4 | the containers check their own indexes and trap `OutOfBounds` on misuse; an obligation a comment unless a decision accepts its arm; `Bytes` has no view at the pin |
| PD-145 | 0.0.4 | `SmallMap` waits for its first consumer |
| PD-146 … PD-148 | — | unused: 0.0.5 proposes none |
| — | 0.0.1a | none: the adoption of `2e1cb4a` takes no decision, and PD-191 … PD-200, its planning dispatch's block, are unused |

## The pin, and what each later landing would move

**Planned at `7e91730`** — the workbench's pin then, landings 83 … 103 — and **re-pinned once, at landing 118**, by
the author's word on the workbench's question 32 (2026-10-15 12:04), so that one adoption carries 104 … 118: the
use-after-free fix (116), the refusal of generic value parameters (117) and the two link fixes (118). **The pin is
`c9baa9e`**, landing 118's commit, taken by the workbench on 2026-10-16 at a quiet point with no claim in flight, and
adopted here the same day, before any subcycle of the cycle started. *(Corrected 2026-10-15 by the pass's
continuation: this said "after landing 115", the author's word of 07:42, which question 32 superseded.)* **The pin is
`2e1cb4a` since the libraries' second re-pin**, landing 140's commit, by the author's word of 2026-10-22 03:49:41
(relayed by `management_2`), taken by the workbench at 04:59 that morning at the quiet point after 0.0.2's step cut,
with no claim in flight: 0.0.0 and 0.0.1 had run at `c9baa9e`, so its adoption is the lettered subcycle 0.0.1a (W-31),
and nothing else is dispatched on this library until it lands. The table
names each place in this cycle's plan a landing would move, so that **the adoption is this list, not a search**, and
its last column says what the adoption measured, row by row. A re-pin is taken **between subcycles**, never inside
one (the early ecosystem audit's EC9: the `7e91730` pin itself was taken mid-cycle elsewhere); a subcycle that has
started finishes at the pin it started at.

| Landing | What it does, by the compiler's notice or the board | What it would move here |
|---|---|---|
| 104 (DEF-249) | an `exit` operand is held to `int32`, `NITPICK-TYPE-007` otherwise | **nothing**: every `exit` operand the cycle's programs write is an `int32` — a literal, a `=>! int32` cast (the size probes' `#size_of`, an `int64`), an `int32` `Result`'s value, an `int32` call — counted by 0.0.0's §1.6 and re-counted by each later subcycle's facts. *At the adoption, at `c9baa9e`: nothing moved* — every program compiled and ran at both legs, and block 0b's count of operands is the same. |
| 105 (DEF-159) | a value stored through a held `@x` after `move(x)` is dropped at the scope's exit; the emission of every function with an address-taken owning binding moves | **no answer moves**: the cycle holds no `@` in a binding (§1.6). What moves is emission: the compiler's own `npkc.ll` digest, which 0.0.1's CI asserts against the pin's row, and any IR byte count a record quotes. *At the adoption:* CI's `npkc.ll` row moved, to notice 118's `1f48a31a…`, 31 731 079 B; and of the cycle's 78 `.npk` files, each compiled as a root at both pins and compared through the compiler's `meta/roadmap/1.6/tools/attrnorm.py` (`git show c9baa9e:`), 65 emit the same IR, 11 are refused at one pin or both, probe 06's differs by landing 118's symbol, and `tests/unit/bytes_put_uint.npk`'s by one drop's guard in `renders`, which takes an owning binding's address — the emission this row says moves; its exit is the same at both pins. |
| 106 (D-342 R1, D-343) | an enum values every variant or none; a macro parameter the body declares is refused | **nothing**: no valued enum variant, no macro. *At the adoption, at `c9baa9e`: nothing moved* — every program of the cycle compiled and ran at both legs, and every refusal kept its codes and sites, as at `7e91730`. |
| 107 (DEF-243) | a builtin named as a value is refused | **nothing**: every builtin is called. *At the adoption, at `c9baa9e`: nothing moved* — every program of the cycle compiled and ran at both legs, and every refusal kept its codes and sites, as at `7e91730`. |
| 108 (DEF-202) | an aggregate `fixed` binding may be initialised by naming another | **newly allowed**, not used: every `fixed` table stays a literal (probe 12); probe 01b's `U64_MAX` is a scalar built from a scalar, which `7e91730` accepts. *At the adoption:* not used, and nothing moved. |
| 109 (DEF-224, D-352) | `failsafe`'s `pick` is found through bare blocks | **newly allowed**, not used: every `failsafe` opens with its `pick`. *At the adoption:* not used, and nothing moved; measured, a `pick` in a bare block is found at `c9baa9e` and `REACH-001` at `7e91730`. |
| 110 (DEF-226) | `pick (r.is_error)` carries the check out | **nothing**: the cycle tests a `Result` with `if (r.is_error)`. *At the adoption, at `c9baa9e`: nothing moved* — every program of the cycle compiled and ran at both legs, and every refusal kept its codes and sites, as at `7e91730`. |
| 111 (DEF-233, DEF-238) | a `give` or `fall` outside its arm is `NITPICK-TYPE-094`; a `frac` member written is `NITPICK-TYPE-024` | **nothing**: none written. At `7e91730` a stray `give`/`fall` ends `npkc` at exit 3 with no message, which a refusal fixture would misread; none is planned. *At the adoption, at `c9baa9e`: nothing moved* — every program of the cycle compiled and ran at both legs, and every refusal kept its codes and sites, as at `7e91730`. |
| 112 (DEF-232; its notice F54; on the compiler's `main` as `958890a`) | a `NIL` member is the zero-sized `{}`, as D-084 says; the checker unchanged | **nothing**: no `NIL` field (`tools/shapes.py`, in each subcycle's facts). *At the adoption, at `c9baa9e`: nothing moved* — every program of the cycle compiled and ran at both legs, and every refusal kept its codes and sites, as at `7e91730`. |
| 113 (its notice F55: DEF-235, DEF-236 (c)(d)(e), DEF-237, DEF-234 (c)) | `NITPICK-PARSE-001` at a keyword declared as a name of ANY kind; `NITPICK-TYPE-045` at a `joins` deadline that is not a constant; `NITPICK-DERIVE-007` at an attribute not named `derive`, and at any attribute on a local binding (`DERIVE-004` at `#[derive]` on an impl); `NITPICK-RESOLVE-014` at an `opaque struct` outside an `extern` block; two texts | **nothing, checked against F55's text and the pin's keyword table**: every declared name of every kind the rule lists, in every `.npk` the cycle's patches add, read against `src/frontend/keywords.npk` at the pin — 170 words, the same set in landing 113's work — by `tools/names.py`, proved on a planted control holding each kind: none is a keyword. Every attribute is `derive`, on a struct or an enum; no `joins`, no `opaque`; and the two `??` the cycle writes, in probe 01b, are on an `Optional`, not a `Result`. *(Corrected 2026-10-15: this row named five words and a local `buffer`, the defects' first reading; F55's rule is every keyword, every kind of name.)* *At the adoption: nothing moved* — the pin's `src/frontend/keywords.npk` is byte-identical to `7e91730`'s, its 170 words; `tools/names.py` finds no declared name among them, and at `c9baa9e` the compiler's own parse sweep (0.0.3) none; an unknown attribute is `NITPICK-DERIVE-007` at the pin, measured, and none is written. |
| 114 (DEF-250; F56) | the D-211 check hoisted out of the initialiser's branch: a module-level binding with no initialiser — `int64:counter;`, and the bare struct, `stack`, `wild`, `wildx`, `pub`, `atomic<int64>` and channel forms — is `NITPICK-TYPE-055` at its declaration | **nothing**: every module-level binding the cycle writes is a `fixed` one with an initialiser, but probe 12b's, a plain one with an initialiser, refused on purpose and `TYPE-055` at the pin already (`tools/rulings.py`). *At the adoption: nothing moved* — probe 12b is `TYPE-055` at 9:1 at both pins. |
| 115 (DEF-251; F57) | every emitted `define` carries LLVM's `null_pointer_is_valid` | **every program's emitted IR moves, by design**: CI's `npkc.ll` row — the compiler's own emission, `b79f89c5…` at `7e91730` — moves with the re-pin as with any; the cycle records no digest or byte count of its own programs' IR, and no comparison of IR across two pins; and 0.0.0's §1.5 recursion edges, which measure the emitted frames at each leg, are re-measured by its block 0b. D-355, `NULL` legal only for `wild` pointers, is a later landing of its own: the cycle writes no `NULL` (`tools/rulings.py`). *At the adoption:* CI's row moved (row 105); the attribute, 1 528 of it on the new side, is the whole difference for 65 of the 67 programs both pins emit (row 105's comparison); and §1.5's four edges are the same at `c9baa9e`. |
| 116 (DEF-252, the use-after-free) | a callee's store of a view into a place its caller owns asks DEF-42's holder-scope question at the call: `NITPICK-BORROW-002` | **probe 08h's verdict** (`tests/probe/defect/view_reseat/`): refused, `NITPICK-BORROW-002`, its right answer — 0.0.3's PENDING refusal on DEF-252, which flips at the adoption of a pin of 116 or later and stays pending below it. *At the adoption:* probe 08h is refused at `c9baa9e`, `NITPICK-BORROW-002` at 30:20, and lands in `refused/` by 0.0.0's own convention (its §3), so 0.0.3's pending refusal is not made, and PD-132's third clause and reversal say what the pin holds. |
| 117 (D-353, with D-354) | a generic value parameter is a RESERVED form, refused by a code of its own, and D-336's corpus admits that verdict | **nothing**: none written; a capacity is a `fixed` constant (the libraries' S-135 answer). *At the adoption, at `c9baa9e`: nothing moved* — every program of the cycle compiled and ran at both legs, and every refusal kept its codes and sites, as at `7e91730`. |
| 118 (DEF-253, with DEF-254) | a synchronous `Self->` method called through a generic bound links; and a trait's default method calling a sibling on `self`, which never linked, links | **probe 06's verdict** (`tests/probe/defect/bound_pointer_receiver/`): it links and runs, exit 0 — 0.0.2's PENDING unit on DEF-253, which flips at the adoption of a pin of 118, and not at a pin below it (the run then reddens to say its marker is stale, and the marker and its line in `harness/baseline/PENDING.txt` go); and nothing for DEF-254: no trait default calls a sibling on `self` (`tools/shapes.py`). *At the adoption:* probe 06 links and runs at `c9baa9e`, exit 0 at both legs, and its controls 5 and 1; it lands in `tests/probe/` with them, as probes 06b and 06c, by 0.0.0's own convention, so 0.0.2's pending unit is not made, and PD-131 says what the pin measures; DEF-254: none written; and DEF-255, which 118 registered open — a qualified trait call through a bound, `NITPICK-TYPE-019` — none written. |
| 119 (D-355; F61) | `NULL` leaves the plain pointer: `NITPICK-TYPE-096` where a plain pointer or an `Optional` is expected, and a pointer that may be absent is `T->?` with `NIL` | **nothing**: the plan's one `NULL`, `vec_free`'s store into `Vec`'s `wild` `items` (0.0.4's step 2), is the legal case. *At the adoption, at `2e1cb4a`: nothing moved* — 0.0.4's units run as at `c9baa9e`, and `tools/rulings.py` counts no other `NULL` in the plan's 78 `.npk` files. |
| 120 (D-360; F62) | the `Optional`'s unwrap-or-trap is `??!` | **newly allowed, not used**: none in the 78 files. *At the adoption: nothing moved.* |
| 121 (D-361 and the `#ptr_add` confinement; F63) | a value of `wild` provenance enters a plain pointer slot only through `=>! T->`, `NITPICK-TYPE-097` otherwise | **nothing**: the plan's one `#ptr_add`, in `src/core/bytes.npk` (0.0.4's step 3), compiles at the pin. *At the adoption: nothing moved* — 0.0.4's blocks read `SAME`. |
| 122 (D-357; F64) | a `comptime func:` exists at compile time only: `NITPICK-TYPE-098` at a call or a name outside a compile-time context | **nothing**: no `comptime` (`tools/rulings.py`). *At the adoption: nothing moved.* |
| 123 (D-356; F65) | a payload-less enum variant is a constant outside the evaluator | **newly allowed, not used**: no module binding names a variant. *At the adoption: nothing moved.* |
| 124 (D-359; F66) | the orphan rule: an impl names a type or a trait its own manifest's tree declares, `NITPICK-TYPE-099` otherwise | **nothing**: every impl the cycle writes sits in the file that declares its type and its trait (`tools/rulings.py`). *At the adoption: nothing moved* — probes 06 … 07 compile and run alike at both pins. |
| 125 (DEF-234 (a)(b); F67) | a driver method may take a byte payload; `use network.connect;` binds its member | **newly allowed, not used**: no `extern`, no logical-path import. *At the adoption: nothing moved.* |
| 126 (DEF-242, DEF-263; F68) | the site table holds the sites the emission holds, its ids renumbered dense; `site_path` answers a view | **every emission's text moves, by design, and no answer**: the cycle calls no `site_path`, `site_line` or `chain_site` and records no digest of its own IR; CI's `npkc.ll` row moves with the pin (0.0.1a's step 1). *At the adoption:* every emission that compiles at both pins is `SAME` through the compiler's `sitenorm.py --site-path-cap`, the reading its row for 126 names — the tree's 26 (0.0.1a's block 3), and at the rehearsal the 67 of the plan's 78 files that compile — each table cut from 294 or more sites to the emission's own. |
| 127 (D-339 / DEF-181; F69) | the lock walk, its holes and its floor closed in nine rules | **nothing**: no lock and no `acquires`. *At the adoption: nothing moved*; 0.0.2's §1.5 sentence on a lock made and never held, three floor calls, measured again at `2e1cb4a`: the same three. |
| 128 (D-341; F70) | a `buffer` is indexed and ranged like a slice of bytes, checked; a `#wild_slice` over a managed header's pointer is a view of its owner | **texts, and no program**: 0.0.4's `Bytes` writes through `.ptr` behind its own checks and takes no view, so it compiles and runs as at `c9baa9e`; the plan's texts that said a `buffer` cannot be indexed or ranged at the pin are re-derived (0.0.4's step 3 and file), `VERIFICATION.md` §2 takes a note (0.0.1a's step 2), and PD-144's text is held for 0.0.4's step cut (0.0.1a.md §8). *At the adoption:* measured — at `c9baa9e` an index and a range are `TYPE-007` and a `#wild_slice` view held across the body's overwrite is accepted; at `2e1cb4a` the index compiles, and either view held across the overwrite is `BORROW-015` there; probe 11 exits 0 at both legs at both pins. |
| 129 (DEF-244; F71) | a root imported back from a sibling directory is one module, loaded once | **nothing**: no module imports one that imports it, and the consumer imports by relative path. *At the adoption: nothing moved*; B7 below is fixed in the pin. |
| 130 (DEF-245, DEF-260; F72) | a declaration whose header fails is one report | **no refusal, one text**: a refusal is judged as a set of codes at their sites (B-7), and 0.0.0's eleven keep theirs at both pins; B-7's note in 0.0.3's step 1, which said DEF-245 "reports" two or three, is re-derived, and PD-140's declined alternative is held for 0.0.3's step cut (0.0.1a.md §8). *At the adoption:* 11 refused alike (0.0.1a's block 3), and 0.0.3's refusal blocks read `SAME`. |
| 131 (DEF-255, DEF-266; F73) | the qualified trait call `Trait.m(x)` reaches a bound and a pointer receiver | **newly allowed, not used**: every trait method is called with the dotted form. *At the adoption: nothing moved*; DEF-255 is fixed in the pin. |
| 132 (DEF-256; F74) | a consuming `pick`'s binding re-assigned after a move is live again | **nothing**: none written. *At the adoption: nothing moved.* |
| 133 (DEF-257, D-362; F75) | a `pick` on a pointer is `TYPE-065`; the pipe operators are struck, `PARSE-014` | **nothing**: no `pick` on a pointer, no pipe. *At the adoption: nothing moved.* |
| 134 (DEF-178, DEF-187; F76) | a `pick`'s value pattern is a constant of the selector's type | **nothing**: the plan's 70 picks, 597 arms, hold no value arm. *At the adoption: nothing moved.* |
| 135 (DEF-190, DEF-182; F77) | a numeral's digit run ends in a digit; an attribute decorates only what keeps one | **nothing**: no numeral ends in `_`, and every attribute is `derive` on a struct or an enum. *At the adoption: nothing moved.* |
| 136 (DEF-258, DEF-259, DEF-261; F78) | a keyword is never a parameter's name, a local `T:keyword` is `PARSE-001` at the name, and a function modifier stands before `func:` alone | **one text**: the `stack` account 0.0.2's step 4 writes, re-measured at `2e1cb4a` (0.0.2's §1.16); no declared name of the plan's 78 files is a keyword of the pin's 170 (`tools/names.py`, against `git show 2e1cb4a:src/frontend/keywords.npk`). *At the adoption:* a local named `stack` is `PARSE-001` at its name where it was `PARSE-002` at the declaration, and a parameter one report where it was two: 0.0.2's six §1.16 lines are the only Expect lines of 0.0.2 … 0.0.5 the pin moved beside its own. |
| 137 (DEF-267; F79) | the awaited and the spawned qualified call reach | **nothing**: no `await`, no `spawn`, no qualified trait call. *At the adoption: nothing moved.* |
| 138 (DEF-272; F80) | an explicit `<-` is a place step to the escape and aliasing analyses | **nothing**: probe 10's four explicit `<-` store no view, and probe 08h's `BORROW-002` stands at 30:20. *At the adoption: nothing moved* — both answer alike at both pins. |
| 139 (DEF-265, DEF-271; F81) | the statement level knows a brace group, and phantom parse reports vanish | **nothing**: each refusal's codes are its first reports. *At the adoption: nothing moved.* |
| 140 (DEF-275; F82) | a pointer's value handed to a callee is checked against the views through it | **nothing**: no call of the plan hands on a pointer's value under a view through it. *At the adoption: nothing moved* — 0.0.4's containers run alike. |
| 141 (DEF-268; `6370cae`) | a function declared inside a body is one report, `PARSE-001` at `func` | **NOT carried.** Would move nothing: no `func:` inside a function's body in the plan's 78 files. |
| 142 (DEF-176; `79cd363`) | a non-folding chain at the depth bound compiles; D-363 and D-364 ratified | **NOT carried.** Nothing: its row's sweep moves no file, and the plan's statements are far below the bound. |
| 143 (DEF-184, DEF-177; `753e783`) | a type nested past 256 levels is one `PARSE-012`; a member is named after a dot | **NOT carried.** Nothing: every member after a dot is a name, and no type nests deep. |
| 144 (DEF-185, DEF-186, DEF-188, DEF-240; `6451911`) | a macro body declares only what an expansion emits; a macro takes no type arguments | **NOT carried.** Nothing: no macro. |
| 145 (DEF-269; `9c08ccc`) | the verified build's encoder holds a chain at the depth bound | **NOT carried.** Nothing: the harness never runs the verified build. |
| 146 (DEF-274, S-134's R4; `915f427`) | an atomic's methods lower through a pointer; `npkc FILE --reach OUT` lists the identities a `failsafe` must name | **NOT carried.** Nothing: no `atomic<`. It offers `--reach`, which could read a consumer's bill where `env.sh`'s `bill` reads `NITPICK-REACH-003`'s message. |
| 147 (DEF-270, DEF-280; `d422c1e`) | a generic `comptime func:` names its type parameter; `move(x)` folds in a comptime body | **NOT carried.** Nothing: no `comptime`. |
| 148 (DEF-279; `aba4a69`) | the verified build's encoder holds a mask at the width's edges | **NOT carried.** Nothing: the verified build is never run here. |
| 149 (DEF-277; `50ebf7d`) | the verified build's statement walk holds a nest of blocks at the depth bound | **NOT carried.** Nothing: as 148. |
| 150 (DEF-276; `ea571d5`) | the emitter holds every chain at the depth bound | **NOT carried.** Nothing: every emission is byte-identical, by its row. |
| 151 (D-363's R1, DEF-212; `9eaf3b6`) | a `pick` arm names several values with one body; a repeated value, variant or identity is `PICK-004`, and a dotted path over a selector that is no enum `TYPE-007` | **NOT carried.** Would refuse nothing: the plan's 70 picks repeat no arm and spell no list, and every dotted arm is a variant or an error identity. It newly allows a `failsafe` arm naming several identities, which the next adoption may weigh for the bills. |

**Also ruled in landing 112's commit** (D-353 … D-359, the board's notice F54), each held to what the cycle writes:
generic value parameters out until designed — 117 above; `NULL` legal only for `wild` pointers (D-355) — one written, the legal case (row 119); a
payload-less enum variant as a constant outside the evaluator — no `fixed` initialiser names a variant; a `comptime func:`
compile-time only — no `comptime` written; the floor through `opt -O2` as its own measured landing — it moves the
runtime object, whose symbols 0.0.2's build step 1 re-measures on every run; and the orphan rule (S-37) — every `impl`
the cycle writes sits in the file that declares its type and its trait (`tools/rulings.py`). *(Corrected 2026-10-15:
this table said "nothing is known" of 114 and 115, and stopped there; the record's entries of 08:06, 08:08, 09:22 and
12:03 say what each is.)* Each is built by a landing in the pin `2e1cb4a`: 117, 119, 122, 123 and 124, rows above.

**Rows 119 … 140, measured at the adoption of `2e1cb4a`** (2026-10-23, by its planner, T12), over every `.npk` of the
plan — the tree's 37, and the 78 that 0.0.0 … 0.0.4's patches leave, in a stand-in at the rehearsal: at `c9baa9e` and
`2e1cb4a` every file compiles, or is refused with the same codes at the same sites; every emission is the same through
the compiler's `sitenorm.py --site-path-cap`; every program exits the same at both legs; and the unchanged plan, run
at `2e1cb4a` with `env.sh`'s pin alone moved, read `SAME` in every block of 0.0.2 … 0.0.5 but each block 0a's commit
line and 0.0.2's six `stack` shapes. Each row's account is the compiler's notice,
read at the landing's commit and its row in the compiler's `meta/NOTICES.md`, beside the workbench board's census
for it, which says "nothing of ours moves" for every one but 124 and 128, whose two moves are `nitpick-time`'s.
**Rows 141 … 151** are the landings past the pin, up to the compiler's `main` at 0.0.1a's planning (`9eaf3b6`, landing
151; the advance notice F94 names 152, not landed), each NOT carried, with what it would move here, read at its commit
and its row there, so that the next adoption starts from a list.

**Built at landing 128, in the pin `2e1cb4a`:** the compiler's D-341 (a `buffer` indexed and ranged, a view frozen like
any other), which 0.0.4's `Bytes` waited on: it may offer a frozen view by a decision (PD-144's reversal), and none has
been taken (row 128).

**At the re-pin, the adoption is:** 0.0.0's blocks 1 … 4 at the new pin (every verdict in its §6), the defect
directories' verdicts (re-derived first: the pin flips each fix it carries), each subcycle's facts block, CI's pinned rows (the commit and the compiler's `npkc.ll` digest,
`b79f89c5…` at `7e91730`), `harness/irscan.py`'s two lists re-classed against the new runtime object (the runner stops on
a symbol neither list holds), and this table's "what it would move" column, row by row. **It was taken at `c9baa9e`
on 2026-10-16, before any subcycle started**, and measured: the two defect directories' probes flipped, each to the
verdict its row predicts — probe 06 runs, in `tests/probe/` with its controls, and probe 08h is refused, in
`refused/`, as 0.0.0's three directories have it (its §3), so neither is a pending unit and no compiler defect is
raised; CI's rows are `c9baa9e91c55…` and notice 118's `1f48a31a…`, 31 731 079 B; and `npkrt.o` is byte-identical at
both pins (`c8e5033a…`), its 119 global symbols each a row of `runtime_symbols.tsv`, so neither of `irscan.py`'s lists
moved. **The second, at `2e1cb4a`, is 0.0.1a**, planned on 2026-10-23 after 0.0.0 and 0.0.1 ran at `c9baa9e`, and
measured at its planning: no verdict, emission or exit moved (rows 119 … 140); CI's rows are `2e1cb4adef79…` and
notice 140's `0073060250f0…`, 32 569 732 B, with LLVM's release asset now held to its sha256, `1ead36b3…`, before it
is unpacked; `npkrt.o` is byte-identical at both pins again, so `irscan.py`'s lists stand; the manifest's
`[toolchain]` rows stay, the compiler's being byte-identical; and two landings move texts the later files write, 136's
and 128's, each re-derived in its file, with PD-140's and PD-144's texts held for their step cuts.

## The shapes this cycle does not write

Open or silent at `7e91730`, the pin this cycle was planned at, from §2.2 of the workbench's planning brief for this
cycle, of 2026-10-15 (A: the answer differs between `7e91730` and later landings, every one of which the pin `c9baa9e`
carries; B: open or silent at `7e91730`, B9 … B12's defects fixed since, by landings 112, 113 and 117; C: already in
it), and the two defects 0.0.0 found. The cycle keeps clear of all of them at `c9baa9e` as at `7e91730`, and at
`2e1cb4a`, where B7's DEF-244, B8's DEF-245 and DEF-255 are fixed too (landings 129, 130 and 131) and B14's D-341 is
built (128). Each
subcycle's facts
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
| B7 a root imported back from a sibling directory (DEF-244, fixed at landing 129) | no module imports a module that imports it; 0.0.3's `check_layering` holds it |
| B8 a header failure reported two or three times (DEF-245, fixed at landing 130) | a refusal fixture asserts the SET of codes (B-7), never a count of reports |
| B9 a `NIL` field (DEF-232) | none written |
| B10 `acquire`, `any`, `trit`, `nit`, a local `buffer` (DEF-235) | none written |
| B11 a `comptime` value parameter, a non-constant `joins`, an unknown attribute, a module-level `opaque struct` (DEF-236) | none written; attribute names counted |
| B12 `??` over a `Result` (DEF-237's advice) | `?!` and `?\|` only |
| B13 `use mod.f;` (DEF-234 (b)) | path forms only: `use "./x.npk".f;` |
| B14 a `buffer` read or written through an untied view (D-341, built at landing 128) | `.ptr` behind the library's own checked accessors; no `#wild_slice`; no returned view |
| B15 wide strings | not spelled |
| B16 compiler documents its own tree contradicts (DEF-239), S-134 | the probes measure; no plan line rests on a reference sentence alone |
| C — `fixed T[]` and `string_bytes`; `TYPE-072` on a clause-less `while`; the six-arm floor; the generic by-value refusals; the symbol scan's blindness to a syscall | 0.0.0's PD-132; every `while` states `decreases`; every program names the floor (0.0.0 §1.4); `Vec<T: Copy>` (0.0.4); a call-edge scan (0.0.2) |
| a synchronous `Self->` method through a generic bound (0.0.0's first defect, DEF-253, fixed by landing 118) | written in probe 06 and its controls, which run at the pin (PD-131), and nowhere else |
| a view re-seated by a callee into a place its caller owns (0.0.0's second defect, DEF-252, fixed by landing 116) | written only in probe 08h, which the pin refuses, `NITPICK-BORROW-002` (PD-132) |
| a qualified trait call through a bound, `Src.step(f)` (DEF-255, which landing 118 registered open, `NITPICK-TYPE-019`, and landing 131 fixed) | none written: every trait method is called with the dotted form — read over every patch's added lines at the adoption |
| a trait's default method calling a sibling on `self` (DEF-254, which links only from 118) | none written: `tools/shapes.py` counts it, with its own planted control (0.0.2 on) |
| a module-level binding with no initialiser, or a plain one (DEF-250 at 114; D-211) | every one `fixed` with an initialiser but probe 12b's, refused on purpose: `tools/rulings.py` (0.0.2 on) |

And `PLAYBOOK.md` §2's rows open at the pin are kept: the read-only view; no part of a `fixed` binding written; every
path leaving explicitly; `main` exactly `int32(cstring[]:_~argv)`; each `Result` tested alone; a qualified `pick` arm;
no literal outside the envelope; `#size_of` measured, never summed; a container's free drops its owners.

## What the audits found owed, and where each is carried

**The workbench's ecosystem audit of 2026-10-15** (`meta/audits/ecosystem-2026-10-15.md` in the workbench) read this
repository's `main`, not this branch: it re-checked E2-4, E2-6, E2-10, E2-13, E2-15, EC2, EC3, ED2 and EK1 and found each
still open there, and raised E3-1 and E3-14. **The plan fixes every one, in the step this table names**; none is carried
past cycle 0.0.

| Item | Carried by | How |
|---|---|---|
| PL-1, the read-only view (E2-2) | 0.0.0 step 4 | every reader, cursor, text and document slot `fixed uint8[]`, measured by probe 08's family; PD-132 |
| PL-2, the writer's sink and `Bytes.view()` | 0.0.0 step 4; 0.0.4 | `put`'s `text` is `fixed` (PD-132); `Bytes` has no view at the pin and its `take` is an owned copy (PD-144) |
| PL-3, the probes the view needs | 0.0.0 steps 2 … 4 | probes 08 … 08h, 12's range, 08f's `TYPE-014` |
| PL-4 and E2-4, LLVM 20.1.8 and the manifest's rows | 0.0.1 | `[toolchain]` with `llvm`, `triple` and `datalayout` as the compiler's `BUILD_REFERENCE.md` §1 gives them, worded as `nitpick-regex`'s manifest; `CLAUDE.md` and `README.md`; CI |
| PL-5, the compiler's state | 0.0.0 step 4 | `BUILD.md` §1 re-read and dated, `README.md`'s status, O-N2 answered, PA-022's note |
| PL-6, `=> dyn` and landing 94 | 0.0.0 step 3 | probe 07 drives an owning implementation through the explicit cast |
| E2-6, where the dogfood consumer lives | 0.0.5's patch 1 | fixes: six lines made PA-103's — the cycle map's, three of the 0.12 roadmap's, and two the claim's subject found (`examples/README.md`, the 1.0 roadmap); its own repository's runner runs it |
| E2-10, counts against sets | 0.0.5's patch 1 | fixes: `ROADMAP.md`'s and `OPEN_QUESTIONS.md`'s copied counts dropped, the entries their own count; the workbench's `LIBRARIES.md` is the orchestrator's (W-16) |
| E2-13, no `CURRENCY.md` | 0.0.1 | `meta/research/CURRENCY.md` created; the library counted security-sensitive and its three research items named, answered at cycle 0.0's first dispatch, before any probe (0.0.0's gate item 7) |
| E2-15, `CLAUDE.md`'s empty heading | 0.0.1 step 6 | the paragraph moved under "What this is" |
| EC2, what an index does | 0.0.0 step 4; 0.0.4 | `SAFETY.md`'s row and `VERIFICATION.md` §2 with probe 11's measurement; every accessor of `Vec` and `Bytes` checks its own index, measured not to trap through a pointer (PD-144) |
| EC3, "every public `error:`" | 0.0.3 | `check_error_budget` keyed by module and name, private identities included (measured: a private identity a reachable `fail` raises is owed as `<module>.<name>`); EC3's sentences and twins, and six more found by the claim's subject (PD-142) |
| ED2, local `O-N` ids | 0.0.0 steps 2 and 4 | O-N2, O-N3 and O-N4 each say their id is this repository's own; nothing takes a registry id |
| ES1, "nothing exists today" | 0.0.0 step 4 | O-N2 struck as answered |
| EK1, `VERIFICATION.md` P-1 | 0.0.4 | P-1 superseded in part by P-1a: an obligation is a comment unless a decision accepts the arm its live clause costs — measured: each of `requires`, `ensures` and `limit` charges every consumer one (PD-144) |
| EC9, a re-pin mid-cycle | this README | a re-pin is taken between subcycles; the landing table is the adoption, and the second's is the lettered 0.0.1a (W-31) |
| E3-1 (= ES1 and PL-5), "no stack guard" | 0.0.0 step 4 | fixes: native recursion traps `StackExhausted` (PD-133); `README.md`'s, `CLAUDE.md`'s and `OPEN_QUESTIONS.md`'s O-N2 sentences restated, O-N2 struck as answered |
| E3-14, the TOML pins | 0.0.1 step 5; 0.0.5's patch 1 | fixes: `CURRENCY.md`'s TOML row (0.0.1), and `FORMATS.md` 15 and 68, the 0.6 roadmap's scope line, and the two its subject found, `README.md`'s format row and `src/format/README.md`, each carry the superseded fact beside the pin; cycle 0.6.0 decides the version |

## The planning brief's open points, and each one's answer

| # | Point | Answer |
|---|---|---|
| 1 | which compiler the plan targets | `2e1cb4a`, the second re-pin, adopted by 0.0.1a; `c9baa9e`, the first, adopted before 0.0.0, by the landing table above; planned at `7e91730` |
| 2 | probe 05's meaning | settled by 0.0.0: refused at `arena_make`, `NITPICK-TYPE-007` (PD-130) |
| 3 | returned reader structs | settled by 0.0.0: a constructor returns its cursor over the bytes it was handed; over its own, `BORROW-001` (PD-132) |
| 4 | `Bytes` and D-341 | settled at `c9baa9e`: a `buffer` could be neither indexed nor ranged (0.0.0's probe 11), so `Bytes` offers no view and its `take` copies (PD-144); at `2e1cb4a` D-341 is built (landing 128), the condition PD-144's reversal names, and no decision has given `Bytes` a view |
| 5 | `#size_of<Event>()` and an enum's width | settled by 0.0.0: four bytes; `Event` 32 (PD-129) |
| 6 | probe 10 against the 8 MiB stack | settled by 0.0.0: 50 000 levels complete; the traps are at 65 535 and 131 063 (PD-133) |
| 7 | the bill, and `IntOverflow` | settled by 0.0.0's oracle measurements (PD-134) |
| 8 | whether `nitpick-regex`'s answer on live contracts (A′, its `VERIFICATION.md` P-1b) binds this library | settled by 0.0.4: it does, as `VERIFICATION.md` P-1a (PD-144) |
| 9 | the `repro` check | settled by 0.0.2: each copy carries its manifest, since without it the consumer's two modules differ — the check's mutant (PD-138, `BUILD.md` B-4) |
| 10 | the undefined-symbol scan | settled by 0.0.2: the call-edge scan stands behind PA-006 and `SAFETY.md` §2, over every module under `src/` and every program, with the runtime's global symbols classed whole — each denied by the facet that forbids it, or the floor's — and the floor and the syscaller its controls on every run; what no call-edge scan can see is named (PD-138, B-2a) |
| 11 | `tools/parse_check` and `tools/check` | settled by 0.0.3: both are compiler sources at the pin, so `npkc` judges the sweep by the code family and the refusals by their codes; `accept` struck (PD-140) |
| 12 | which harness runs the dogfood consumer | settled by 0.0.5: its own repository's, under `nitpick-apps` (PA-103); this library's harness runs `tests/conformance/` and reaches into no other repository |
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
| [0.0.0](0.0.0.md) | **The language probes** — the specification's shapes asked of the compiler at the pin, the flagship among them | a verdict per probe, the specifications amended by them; the two compiler defects of `7e91730` fixed in the pin |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's toolchain rows and test table, CI, `CURRENCY.md` | `npkc` compiles an empty library and a program that imports it |
| [0.0.1a](0.0.1a.md) | **The adoption of `2e1cb4a`** (W-31) — CI's pin and LLVM's asset by content, 0.0.0's dated lines, the old-pin leg on `c9baa9e` | every verdict, emission and exit the same at both pins; CI green at the new pin |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build, the `program` stage, the toolchain pin, `repro` | one test program builds, links, runs, and its exit code is judged |
| [0.0.3](0.0.3.md) | **The harness, part 2** — the refusal and parse stages, the self-check, the tree checks | the self-check proves the harness can fail |
| [0.0.4](0.0.4.md) | **`src/core/`** — `limits.npk`, `Vec<T>`, `Bytes`; `SmallMap<K,V>` waits for its consumer (PD-145) | the primitives, with their suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

The 0.0.2 … 0.0.5 items are the re-derivation's targets, drawn from the audits' owed items and 0.0.0's verdicts; each
file states its own acceptance when it reaches the pin, and where the two differ, the file at the pin governs.

### 0.0.0 — the probes
- [x] `tests/probe/probe01a_naive_accumulate.npk` traps `IntOverflow` (93) and `probe01b_checked_accumulate.npk` exits 0 — **the flagship**
- [x] `probe02_pod_event.npk`, `probe03_payload_enum.npk`, `probe04_arena_pod.npk` — the specification's `Event`, `Step` and `Node`, each probe's exit code its size: 32, 36, 64
- [x] `refused/probe05_arena_owning.npk` — refused at the make, `NITPICK-TYPE-007`
- [x] `probe07_trait_dyn.npk` — the `Format` shape through `dyn`; and `probe06_trait_bound.npk` with its two controls — the same through a bound, a compiler defect at `7e91730` that the pin fixes
- [x] `probe08_view_edges.npk` and its seven refusals, 08h's among them — the read-only view at every edge a reader uses
- [x] `probe09_generic_move.npk` and the capped pair `probe09b`/`probe09c` — owners in a generic `Vec`, and the free that must drop them
- [x] `probe10_explicit_stack.npk` exits 0 at 50 000 levels; `probe10b_native_recursion_traps.npk` traps `StackExhausted` (106)
- [x] `probe11_bytes_growth.npk` — a million appends, twenty reallocations
- [x] `probe12_module_fixed.npk` and its three refusals — a `fixed` table read and ranged; a plain module binding `NITPICK-TYPE-055`
- [x] every verdict in `0.0.0.md` §6 re-measured, SAME, and every consequence in `meta/specs/` and `meta/DECISIONS.md` in the commit of its verdict
- [x] `tests/probe/README.md`; block 6's sweep read
- [x] the three research digests filed before any probe runs, each printed by block 0a with its sha256, the three this plan holds (PD-137)

### 0.0.1 — the skeleton
- [x] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list)
- [x] every `src/` subdirectory has a placeholder module that compiles, so the parse sweep has something to sweep
- [x] `nitpick.toml`'s `[toolchain]` pinned to LLVM 20.1.8 with the `triple` and `datalayout` rows, and its `[[test]]` table's first entries
- [x] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles, links, runs and exits 0, with a comment naming O-N1
- [x] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.8 and the compiler built from the pinned commit, every hex value quoted
- [x] `meta/research/CURRENCY.md`, its three research rows each linking its digest, and its research section saying what each digest found and where each finding is held
- [x] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended

### 0.0.1a — the adoption of `2e1cb4a`
- [ ] CI's three rows at `2e1cb4a` and notice 140's `npkc.ll` row; LLVM's release asset held to its sha256 before it is unpacked, the cache keyed on it, `CURRENCY.md`'s row and its digest
- [ ] cycle 0.0.0's 19 notes re-dated to 2026-10-17, and its ten decision sites each with an added dated note, their text unchanged
- [ ] the old-pin leg on `c9baa9e`: no verdict moved, every emission the same through `sitenorm.py --site-path-cap`, the same exits
- [ ] CI green at the new pin, its first run's install step and emission quoted

### 0.0.2 — the harness, part 1
- [ ] `harness/run.py`, `manifest.py`, `toolchain.py`, `expect.py`, `build.py`, `irscan.py`, `elf.py`, `stages.py`, and `baseline/`
- [ ] one program object and `npkrt.o` per link, every argv built from the manifest's flag lists, every module the manifest's target rows
- [ ] the undefined-symbol scan and the call-edge scan as build steps, over every module under `src/` and every program, the floor and the syscaller their controls on every run
- [ ] the `program` stage at -O0 and again under `opt -O2`, same exit required; `expect-exit`, `stress` and `mem-cap-mib` honoured
- [ ] the `repro` check: two builds from different working directories, each copy with its manifest — and **seen to fail** without it
- [ ] 0.0.0's `tests/probe/` green as the first real `program` suite, probe 06 and its controls among it; the reviewed list naming no unit at the pin, and every way the pending mechanism can be wrong seen red
- [ ] CI's harness step asserting the runner's unqualified green summary
- [ ] `irscan.py`'s two lists class the runtime's global symbols whole, and each denied facet a source construct reaches seen red
- [ ] cycle 0.0.1's twelve items carried out as the libraries' seat ruled them (steps 3 and 4)

### 0.0.3 — the harness, part 2
- [ ] the parse sweep (`npkc` over every `.npk`, judged by the diagnostic's code family) and the refusal stage with the **exact-code** rule (B-7, a set at its sites); `accept` struck
- [ ] 0.0.0's `refused/` judged by its codes, probe 08h among them; the runner refusing a manifest with no sweep
- [ ] `--only`, and output that says twice that a filtered run concludes nothing and never the green summary
- [ ] `harness/selfcheck.py`, its sixteen live cases each **seen red** and its four pending printed as pending; it runs before any judgment, and a live case not red stops the run
- [ ] `check_layering`, `check_error_budget` (keyed by module and name), `check_constants_named`, `check_no_raw_accumulate`, `check_no_recursion` and `check_specs_current` live, each saying what it read; `check_no_owning_fields` from 0.2
- [ ] EC3's sentences corrected; each mutant red by the check it breaks

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — the eight bounds of `specs/SAFETY.md` §7, each with its row; `VALUE_MODEL.md` D-16's ninth joins it in cycle 0.4 (PD-143)
- [ ] `src/core/vec.npk` — `Vec<T: Copy>`, every accessor boundary-tested at `0`, `count-1` and `count`, a misuse trapping `OutOfBounds`
- [ ] `src/core/bytes.npk` — `Bytes` over `buffer` through `.ptr`, `put_uint` allocation-free, growth doubling and counted, no view
- [ ] `SmallMap` deferred to its first consumer (PD-145), and no document saying `src/core/` holds it
- [ ] every obligation written as a comment in the syntax it would take, with a unit standing in (`VERIFICATION.md` P-1a)
- [ ] every unit exits as it expects at both legs; the forgotten free traps `WildLeak`; each mutant red by a unit

### 0.0.5 — close
- [ ] every probe verdict reconciled against the specifications by **reading them**, 01a and 05 by name
- [ ] E2-6's six lines PA-103's, E2-10's counts left to their sets, E3-14's pins with the superseded fact beside them
- [ ] the cycle's findings written as a numbered list; the close audit run and triaged (W-22); a full green run, its output quoted
- [ ] the sweep over the close's patch, before any commit of the worker's own
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes, its gate naming PD-137's three research digests with their dates (each stale ninety days after its own)
- [ ] cycle moved to `done/0.0/` by the last block, every reference to it moved, `ROADMAP.md` updated

## Gate

**The cycle is complete when**: probe 01 has demonstrated the trap and its absence; a full `harness/run.py` is green;
the self-check proves the harness fails in every live way it names and reports the pending ones as pending;
`src/core/`'s containers, `Vec` and `Bytes`, each have a suite (`SmallMap` waits for its consumer, PD-145); and every probe has a recorded verdict with its consequences
written into the specifications.

## Watch for

- **Probe 05 and probe 08h are expected to be refused, probe 01a and probe 10b to trap, and probe 06 to run** — at
  `7e91730` probes 06 and 08h showed compiler defects, which the pin fixes. All are *results*. A subcycle fails only on a verdict that is **undecided** — a compiler crash, a
  hang, or output nobody can read — or one that differs from its plan's Expect.
- **A probe that fails is a finding, not an obstacle.** Record the exact diagnostic, decide the design change, amend
  the specification, and only then continue. Working around a compiler refusal in library code is what the compiler's
  own R6 forbids.
- **The reserved words will bite in `src/core/` specifically**: `end`, `in`, `limit`, `any`, `buffer`, `raw`, `move`
  and `stack` are all words a container library reaches for. `specs/BUILD.md` §7 has the substitutes — use `hi`,
  `src`, `bound`, `frames`.
- **`Vec<T>`'s block is `wild` storage** and every path out of a function that took some must release it, or `exit 0`
  traps under D-151 — a gate on the `wild` half only. A managed body is invisible to it (probes 09b and 09c).
