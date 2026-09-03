# Cycle 0.0 — Foundations

**The probes, the harness, and `src/core/`.** Nothing in this cycle parses
anything. What it produces is the ability to find out whether the rest of the
plan is buildable, and the machinery every later cycle is tested by.

## Why this shape

Two of the compiler project's most expensive lessons decide this cycle's
contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4
  was mostly repair, and every repair dated to the cycle that had parsed the
  construct. `nparse`'s design leans on several language shapes that have never
  been exercised in this combination — a 24-byte POD in a `Vec`, an arena whose
  `get` copies POD nodes, a payload enum in a fixed array, a trait with a
  `Self->` receiver reached through `dyn`. **0.0.0 asks the compiler about all
  of them before anything is built on them.**
- **"Diagnostics come first, not last — they are how every later cycle is
  tested."** Here that is the harness. A suite written after the code is a suite
  shaped by the code.

**One probe is different from the rest and is the reason the cycle opens with
them.** Probe 01 is not asking whether a shape *compiles* — it is demonstrating
that the naive decimal accumulator **traps** on a long number and that the
checked helper **does not**. That is `PA-012`, the library's central
correctness claim, established as a fact on day one rather than asserted in a
document.

## Decisions in

PA-001 … PA-009, PA-012, PA-021, PA-022, PA-030. All settled.
**Nothing in this cycle is blocked on a question.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — twelve programs asking the compiler whether the design is spellable, and one proving the no-trap claim | a recorded verdict per probe, and any design change the answers force |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's test table, CI | `npkc` compiles an empty library and a program that imports it |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build, the `program` stage, the toolchain pin, `repro` | one test program builds, links, runs, and its exit code is judged |
| [0.0.3](0.0.3.md) | **The harness, part 2** — `parse`, `accept`, `check`; the self-check; the tree checks | the self-check proves the harness can fail, eight ways |
| [0.0.4](0.0.4.md) | **`src/core/`** — `limits.npk`, `Vec<T>`, `Bytes`, `SmallMap<K,V>` | the primitives, with their suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the spec amendments the probes forced, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

### 0.0.0 — the probes
- [ ] `probe/probe01_no_trap_accumulate.npk` — **the flagship**: the naive `acc * 10 + d` traps on a 23-digit literal (recorded), and `scan_mul_add`'s shape does not
- [ ] `probe/probe02_pod_event.npk` — a 24-byte POD struct in a `Vec`: fill 100 000, read, copy, compare, clear; `#size_of` asserted at 24
- [ ] `probe/probe03_payload_enum.npk` — a tagged enum with a struct payload (`Step`'s shape), destructured in a `pick`, stored in a `Vec`, `#size_of` recorded
- [ ] `probe/probe04_arena_pod.npk` — an `arena<Node>` of 56-byte POD nodes: `alloc`, `put`, `get` (**the copy**), `free`, a stale handle answering `StaleHandle`, `destroy`
- [ ] `probe/probe05_arena_owning.npk` — an arena whose element holds a `string`; **expected refused**, with the code recorded — this is what forces PA-030
- [ ] `probe/probe06_trait_bound.npk` — a trait with a `Self->` receiver, two impls, called through a generic bound
- [ ] `probe/probe07_trait_dyn.npk` — the same trait through `dyn`, proving `Format` is object-safe (PA-071)
- [ ] `probe/probe08_slice_edges.npk` — a `uint8[]` borrow at the four escape-analysis edges: passed down (legal), returned (refused), stored past the call (refused), held in a struct that outlives it (refused)
- [ ] `probe/probe09_generic_move.npk` — `move T:v` into `Vec<T>` with `T` scalar and `T` owning, including the container's drop
- [ ] `probe/probe10_explicit_stack.npk` — a 50 000-deep nested structure built and freed with an explicit stack, exiting 0; and the recursive version's failure recorded
- [ ] `probe/probe11_bytes_growth.npk` — a million single-byte appends with the reallocation count bounded (the compiler's quadratic-capture defect is why)
- [ ] `probe/probe12_module_fixed.npk` — a `fixed` module-level table read from ordinary code, and a **plain** module binding refused (D-211), with the code recorded
- [ ] a verdict line per probe recorded in `0.0.0.md`, with the exact diagnostic where one was refused
- [ ] every design consequence written into `meta/specs/` **and** `meta/DECISIONS.md` before 0.0.1 starts

### 0.0.1 — the skeleton
- [ ] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list)
- [ ] every `src/` subdirectory has a placeholder module that parses, so the `parse` stage has something to sweep
- [ ] `nitpick.toml`'s `[[test]]` table has its first entries (`probe`, `conformance`)
- [ ] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles, with a comment naming O-N1
- [ ] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.2 and the compiler built from a **pinned commit**, not a branch
- [ ] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended (both were written at repository setup; this is the check that they are still true)

### 0.0.2 — the harness, part 1
- [ ] `harness/manifest.py` — a minimal TOML reader, the schema check, a loud refusal naming any key the schema lacks
- [ ] `harness/toolchain.py` — asks `llc`/`opt`/`ld.lld` their versions and refuses a mismatch against `[toolchain] llvm`
- [ ] `harness/elf.py` — the ELF64 undefined-symbol reader and the allowlist derived from `runtime/npkrt.ll`
- [ ] the build pipeline, every argv built from the manifest's flag lists (B-1)
- [ ] the undefined-symbol scan as a **build step** (B-2) — and note in the record how nearly vacuous it is for this library, since `nparse` makes no syscall
- [ ] the `program` stage at -O0 and again under `opt -O2`, same exit required (B-3)
- [ ] `// expect-exit:` and `// stress: N` honoured
- [ ] the `repro` check: two builds from different working directories, byte-identical IR — and **seen to fail** once, by hand, against a deliberately non-deterministic edit
- [ ] `tests/probe/probe02_pod_event.npk` green as the first real `program` case

### 0.0.3 — the harness, part 2
- [ ] the `parse` stage over every `.npk` in the tree, each file once
- [ ] the `accept` and `check` stages with the **exact-code** rule (B-7)
- [ ] `--only`, and output that says twice that a filtered run concludes nothing
- [ ] `harness/selfcheck.py` with all eight cases from `specs/TESTING.md` V-19, three of them pending until the stages they test exist (`roundtrip` ×2, `corpus`)
- [ ] the self-check runs **first**, and a pending case prints as pending rather than passing
- [ ] `check_layering` — every `use` edge against `specs/BUILD.md` §6's diagram, **including the `format` ↛ `doc` arrow**
- [ ] `check_error_budget` reading `specs/SAFETY.md` §3's table (two identities)
- [ ] `check_constants_named` — no bound outside `src/core/limits.npk`
- [ ] `check_no_owning_fields`, `check_no_raw_accumulate`, `check_no_recursion` — all three live with nothing yet to check, which is the right answer and not a reason to skip

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — every constant from `specs/SAFETY.md` §7, each with the rule that set it
- [ ] `src/core/vec.npk` — `Vec<T>`: `init`, `reserve`, `push`, `pop`, `at`, `set`, `truncate`, `clear`, `insert`, `remove`, `swap_remove`, `fill`, `free`
- [ ] `Vec<T>` exercised at both `T` shapes: a scalar, and an owning value with `move T:v`
- [ ] every accessor boundary-tested at `0`, `count-1` and `count`
- [ ] `src/core/bytes.npk` — `Bytes`: `init`, `push`, `extend`, `extend_str`, `put_uint`, `len`, `view`, `take`, `clear`, `free`
- [ ] `put_uint` allocation-free and correct at 0, 1, 9, 10, 99, 100 and `uint64` maximum
- [ ] `Bytes` growth amortised linear, measured, with the reallocation count bounded (probe 11's shape as a permanent test)
- [ ] `src/core/smallmap.npk` — fixed-capacity, ordered, `EParseState` on overflow
- [ ] every accessor's bounds obligation written as a comment in the `requires`/`ensures` syntax it will take (`specs/VERIFICATION.md` P-1), with a property test standing in
- [ ] every suite program exits 0, so a leak on any path is a trap (D-151)

### 0.0.5 — close
- [ ] every probe verdict reconciled against the specifications by **reading them**, not by remembering
- [ ] the cycle's findings written as a numbered list
- [ ] a full green run, verdicts committed
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes
- [ ] cycle moved to `done/0.0/`, `ROADMAP.md` updated

## Gate

**The cycle is complete when**: probe 01 has demonstrated the trap and its
absence; a full `harness/run.py` is green; the self-check proves the harness
fails five live ways and reports three as pending; `src/core/`'s three
primitives each have a suite; and every probe has a recorded verdict with its
consequences written into the specifications.

## Watch for

- **Probe 05 is expected to be refused and probe 01 is expected to trap.** Both
  are *results*. The subcycle fails only if a verdict is **undecided** — a
  compiler crash, a hang, or output nobody can read.
- **A probe that fails is a finding, not an obstacle.** Record the exact
  diagnostic, decide the design change, amend the specification, and only then
  continue. Working around a compiler refusal in library code is what the
  compiler's own R6 forbids.
- **The reserved words will bite in `src/core/` specifically**: `end`, `in`,
  `limit`, `any`, `buffer`, `raw`, `move` are all words a container library
  reaches for. `specs/BUILD.md` §7 has the substitutes — use `hi`, `src`,
  `bound`.
- **`Vec<T>` is `wild` storage** and every path out of a function that took some
  must release it, or `exit 0` traps under D-151. The suite's programs exit 0 on
  purpose so a leak turns a pass into a trap.
