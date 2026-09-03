# Building, testing, and the module conventions

How `nparse` is built today, how it will be built when the tooling catches up,
and the file-and-import conventions everything in `src/` follows.

---

## 1. What cannot build this yet, measured

Read at the compiler's commit for cycle 1.5.0 (2026-09-03):

- **`npkg build` is the compiler's own bootstrap ladder.** It assembles
  `runtime/npkrt.ll` and `bootstrap/seed/stage1.ll` into a builder, has that
  builder compile `[build] entry`, scans, links, and names the result `npkc`.
  There is no generic-project path and no `target = "library"` behaviour; the
  key is accepted by the schema and read by nothing.
- **`[dependencies]` resolves to nothing.** The loader's dependency-root list
  (`RootList`, `src/frontend/resolve_path.npk`) is created empty in
  `src/driver/pipeline.npk` and `rootlist_add` is never called from anywhere.
  A `use "nparse/scan.npk"` path — the dependency-root form — therefore resolves
  against an empty set. Only `./` and `../` paths work.
- **`npkg` has no `install` and no `update`.**

None of this is a criticism of `npkg`; it was built at 1.4.8 to run the
compiler's own suite, and D-206 scoped it to exactly that. It is written down
because a plan that assumes tooling it has not checked is a plan that discovers
the gap at the first step.

**Decision PA-003: `harness/` builds and tests `nparse` until `npkg` can, and
retires into it.** That is precisely the relationship `bootstrap/harness/` has
to `npkg` in the compiler repository, including the part where both run side by
side and a parity stage holds them to each other before the older one is
retired. Writing the harness in Python is not a dependency violation:
**zero-dependency governs the artifact, not the workbench** (the compiler's
`ORCHESTRATION.md` §6 says so in as many words, about valgrind), and the
compiler's own harness is Python for the same reason.

---

## 2. The build, step by step

```
src/lib.npk  (and every module it reaches by `use`)
   → npkc              →  build/nparse.ll        the emitted LLVM IR text
   → opt -O2           →  build/nparse.opt.ll    only on the check leg
   → llc               →  build/nparse.o         at the manifest's flags
   → undefined-symbol scan against the runtime allowlist
   → ld.lld -static    →  build/<program>        one program object + npkrt.o
```

**Rule B-1.** Every tool invocation is built from `nitpick.toml`'s
`[toolchain]` lists. No tool ever runs at its own defaults — `llc` defaults to
`-O2` and would optimise a build the manifest declined, which cost the compiler
project a measured 25× on one module.

**Rule B-2.** The undefined-symbol scan is a **build step, not a test**. Every
object is scanned and the build fails on any undefined symbol outside the
runtime allowlist derived from `runtime/npkrt.ll`'s own `define`s plus `main`.
This is what makes "no C, ever" a structural property rather than a convention.
For `nparse` it should be nearly vacuous — the library makes no syscall at all
(`SAFETY.md` §2) — and **a symbol appearing here is therefore a finding**, not
a routine pass: it means something reached for the floor that had no business
doing so.

**Rule B-3.** The optimised leg runs on every program, every time: the same
program re-emitted through `opt -O2` + `llc -O2` must produce the **same exit
code**, and the zero-dependency scan is repeated on the optimised object
because `opt` may mint libcalls. This is the compiler's 1.3.8 instrument, and
its first run there found a real defect that had passed for six cycles.

**Rule B-4 — reproducibility.** Two builds of the same tree from different
working directories produce byte-identical IR. `nparse` inherits this from the
compiler (D-078, D-204, D-236) and the harness has a `repro` stage that
measures it, because a property nobody measures is a property nobody has.

---

## 3. Test stages

The harness mirrors the compiler's stage vocabulary
(`BUILD_REFERENCE.md` §7.1) so that the eventual move to `npkg` is a change of
runner and not a change of suite, and adds two of its own.

| Stage | Directory | Passes when |
|---|---|---|
| `parse` | every `.npk` in the tree | accepted by `tools/parse_check` with no diagnostic |
| `accept` | `tests/conformance/` | accepted by `tools/check` in silence |
| `check` | `tests/rejection/` | refused by the frontend with **exactly** the expected codes |
| `program` | `tests/unit/`, `tests/probe/`, `tests/fixtures/` | emitted, scanned, assembled, linked, run at -O0 and again under `opt -O2`, the same exit both times |
| `roundtrip` | `tests/roundtrip/` | **ours** — parse, print, parse again, and the second parse's event stream equals the first's (`WRITER_MODEL.md` §4) |
| `corpus` | `tests/corpus/<name>/` | **ours** — every case in a vendored conformance corpus is judged as the corpus says, with a per-corpus expected-pass count that must match exactly |

**Rule B-5 — expectations live in the test file.** The marker grammar is the
compiler's, marker for marker, plus two of ours:

```
// expect-exit: 7            the exit a run must produce (0 when absent)
// expect-error: NITPICK-TYPE-046
// expect-error-at: 14:9
// stress: 40                run it that many times, the SAME answer every time
// expect-roundtrip: json    the format whose fixed point this case asserts
// expect-fault: DepthExceeded   the ParseError code this input must produce
```

**Rule B-6 — assert on codes and exit codes, never on message text.**

**Rule B-7 — unexpected diagnostics fail a test as surely as missing ones**
(D-237). The set of codes a rejection test reports must **equal** the set its
expectations name.

**Rule B-8 — the harness is itself tested** (`TESTING.md` §7). A self-check
feeds it wrong expectations and requires it to report every one as a failure,
and it runs first.

**Rule B-9 — a corpus count is exact.** A `corpus` entry names how many cases
must pass, and both a regression and an *unexpected improvement* fail the run.
An unexpected improvement is a real event — it usually means a case was
reclassified — and it must be looked at rather than absorbed.

---

## 4. Dependencies

**Rule B-10 (PA-005).** `nparse` depends on the language, its prelude, and
nothing else. `[dependencies]` is empty and stays empty until a decision says
otherwise. That includes, specifically and deliberately:

- **not the compiler's `src/`.** `npkg` imports `../src/frontend/list.npk`
  because `npkg` lives in that tree; `nparse` does not, and reaching into a
  compiler's internals for a growable array would couple this library's
  correctness to a file whose header says it exists for the compiler's own
  tables.
- **not the compiler's `lib/`**, which is scheduled to move to an `nlibc`
  sibling repository (the compiler's `LAYOUT.md` says so), so importing it
  today is importing a path that will change. `nparse` needs nothing from it
  anyway: it makes no syscall.
- **not `nregex`.** A parser that needed a regex engine to tokenize would be a
  parser that had stopped being a parser — the formats here are all scannable
  by a hand-written cursor, which is faster, smaller and provable. The
  prototype's `nparse` did wire a Thompson NFA in as a lexer backend; that was
  for a general *language* front end (§5), which this library is not.
- **not `ntime`.** TOML has four datetime types and `ntime` will one day own
  them. The overlap is real and is recorded as O-P4, not resolved by a
  dependency that cannot resolve. See `FORMATS.md` §4.

**Rule B-11.** The prelude is fair game: `Ordering`, the derivable traits,
`string_bytes`, `string_concat`, `string_equals`, `int_to_string`,
`buffer_new`, the named errnos, and `Result`/`Optional`. Every module has it
bound with no import.

---

## 5. Storage primitives

**Rule B-12 (PA-004).** `nparse` declares its own, in `src/core/`:

- **`Vec<T>`** — `{ wild T->:items; int64:count; int64:cap; }`. The compiler's
  `List<T>` in shape, because that shape is right and has been exercised across
  twenty-two families; **ours** because a library must not import a compiler's
  internals. Operations: `init`, `reserve`, `push`, `pop`, `at`, `set`,
  `truncate`, `clear`, `insert`, `remove`, `swap_remove`, `fill`, `free`.
- **`Bytes`** — an owning byte sink over `buffer`, with `push`, `extend`,
  `extend_str`, `put_uint`, `len`, `view`, `take`, `clear`, `free`. It is the
  parser's scratch and every writer's output. It exists because `string_concat`
  allocates per call: the compiler measured exactly this shape as quadratic in
  `npkg`'s first full run, seventeen minutes of fifty-six spent in the kernel.
- **`SmallMap<K, V>`** — a fixed-capacity ordered association list. Not a hash
  map, and **there is no hash map anywhere in the language or the prelude to
  fall back on** — see `VALUE_MODEL.md` §5 for what a `Document` does about
  large maps.

**Rule B-13.** `nparse` declares no other container. The `Document` tree is an
`arena<Node>` with `Handle<Node>`, which is what the language provides for
graph-shaped data.

---

## 6. Modules, files, imports, and the layering

**Rule B-14.** One module per file, and **a file's `mod:` name must equal its
basename** — the loader reports `NITPICK-RESOLVE-005` at line 1 otherwise, and
says nothing about the name.

**Rule B-15.** Public names carry the module's short prefix and nothing else
carries it: `scan_next`, `event_kind`, `doc_get`, `json_reader`, `emit_json`.
A `pub struct` takes PascalCase (`Cursor`, `Event`, `Document`, `ParseError`).
Constants are `SCREAMING_SNAKE`.

**Rule B-16 — imports are relative today.** Until dependency roots are
populated (§1), every internal import is `use "./x.npk".*;` or
`use "../y/z.npk".*;`, and a **consumer** imports `nparse` by a relative path
to its `src/lib.npk`, which `pub use`s the public surface. Every such site
carries a comment naming O-N1 so the day it lands the change is greppable.

> **`use` is not transitive** (`MODULE_REFERENCE.md` §2.3): a symbol imported
> into a module is not re-exported. `src/lib.npk` therefore has to re-export
> deliberately, which is a feature — the public surface is a list in one file
> that a reviewer can read.

**Rule B-17 — the layering, and the direction of every arrow.**

```
   emit ──────────────┐
     │                ▼
  format ──►  doc ──► event ──► diag ──► scan ──► core
     │                 │                   ▲        ▲
     └─────────────────┴───────────────────┘        │
                                                    │
                       (core depends on nothing) ───┘
```

`core` depends on nothing. `scan` depends on `core`. `diag` depends on `scan`
(for `Span`) and `core`. `event` depends on `diag`, `scan`, `core`. `doc`
depends on `event` and below. `format` depends on `event` and below — **never
on `doc`**, because a streaming consumer must be able to import a format
without pulling in the tree. `emit` depends on `doc` (it prints a tree) and on
`event` (it can also print a stream). A module may not import one to its right.

**Rule B-18 — `format` may not import `doc`.** Stated separately because it is
the arrow most likely to be drawn by accident, and drawing it would make every
streaming consumer link the arena and the tree.

**Rule B-19 — a `use` cycle is legal** (D-086) and is still a decomposition
mistake. The harness checks the layering against this diagram on every run,
because the compiler's experience is that a layering violation arrives as a
cycle six months after somebody moved one function.

---

## 7. Reserved words that will bite

The compiler's list, filtered to the ones a parsing library reaches for. Each of
these reads like an ordinary local name and is not:

| Wanted as a name | Actually |
|---|---|
| `end` | the `when`/`then`/`end` terminator — and **every span, range and token wants to be called `end`** |
| `in` | the `for … in` keyword — and "in" is what every byte source wants to be called |
| `error` | the declaration keyword; `Result`'s field is `.err` |
| `limit` | the verification keyword — and every bound wants it |
| `any` | the type — and a matcher wants it |
| `buffer` | the owning byte cell **type** |
| `raw` | the unwrap keyword — and "raw string" is TOML and YAML vocabulary |
| `move`, `drop`, `pass`, `fail`, `relay`, `give`, `pick`, `fall` | keywords |
| `is`, `is_err`, `defaults`, `as`, `with`, `where`, `never`, `fails` | keywords |
| `mod` | the module keyword |
| `unit` | the unit-declaration keyword |
| `on` | a keyword — `Node?:on = …` does not parse |
| `Self`, `Result`, `Optional`, `Handle`, `arena` | type keywords |
| `trit`, `nit`, `oflags`, `prot`, `mflags`, `fmode` | type keywords |

The names this library therefore uses instead, fixed here so they are used
consistently: **`hi`** for a range's upper bound (never `end`), **`src`** for a
byte origin (never `in`), **`sink`** for a byte destination, **`fault`** for a
parse failure value (never `error`), **`bound`** for a limit, **`kind`** for a
discriminant, **`depth`** for nesting, **`tok`** for a token, **`lit`** for a
literal's text.

---

## 8. Three more shapes that are not what a C or Rust habit expects

- **Adjacent string literals do not concatenate.** `"a" "b"` is two literals.
  A writer builds with `Bytes`, not by juxtaposition.
- **`discard(expr);` takes parentheses; `defer { … }` takes no trailing
  semicolon.** Both wrong forms are parse errors.
- **Struct/trait/impl/function declarations end `};`. Control-flow blocks do
  not.** A semicolon after an `if`'s closing brace is a syntax error.

---

## 9. Open items

- **When `npkg` can build a library** — the trigger to migrate off `harness/`
  is `npkg build` honouring `target = "library"` and `[dependencies]`
  populating the resolver's root list. Neither is on the compiler's 1.5 or 1.6
  map, so this is a request to be made, not a date to wait for. It is the
  **compiler's** question rather than ours and is tracked in
  `../OPEN_QUESTIONS.md` as **O-N1**; nothing here is blocked on it, because
  PA-003 already decided what to do meanwhile.
