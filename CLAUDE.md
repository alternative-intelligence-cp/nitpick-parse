# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

`nparse` — a multi-format parsing library for **Nitpick**, the safety-critical
systems language at `../../nitpick`. **Status: planning.** No library code
exists yet. The specifications and the plan do.

The shared house rules for every library in this ecosystem are
`../PLAYBOOK.md`; this file is what is specific to `nparse`.

## Read these first, in this order

1. **`meta/specs/SAFETY.md`** — the constraints and where they come from,
   including the two rules that shape this library more than anything else: a
   syntax error is a *value*, and arithmetic on attacker-supplied input must
   not trap.
2. **`meta/specs/README.md`** — the index and the reading order for the rest.
3. **`meta/DECISIONS.md`** — every settled design decision with its reasoning.
   **Read this before proposing a change**, because it is recorded why.
4. **`meta/roadmap/ROADMAP.md`** — the cycle map; then the current cycle's
   `README.md`.
5. **`meta/OPEN_QUESTIONS.md`** — what is not settled, each with a
   recommendation.

## The rules that are not negotiable

- **The specifications are the authority** (PA-002). Code that disagrees with
  `meta/specs/` is a defect in the code. A specification that turns out to be
  wrong is amended by a decision recorded in `meta/DECISIONS.md`, in the same
  commit — never by editing the text and moving on, and never by a comment.
- **A settled decision's text is never rewritten.** Supersede it with a new
  numbered decision that says why. This is the compiler's D-085/D-202 pattern.
- **Two public error identities, and no input can produce either** (PA-008).
  `EParseState` and `EParseEncode` fire only on programmer misuse. Every
  condition an input can cause is a `Fault` value the caller must handle by
  `pick` exhaustiveness. **Adding a third is a major version and needs a
  decision saying why a shutdown handler would treat it differently.**
- **No arithmetic in this library may trap on any input** (PA-012). Plain
  integer overflow traps in Nitpick (D-210), so every accumulation is
  range-checked *before* the multiply and the overflow answer is a `Fault`.
  This is the single most likely place to write a remote crash.
- **No native recursion on input-controlled depth** (PA-022). Explicit stacks,
  stated bounds. `[[[[[…` is the oldest trick there is and the language has no
  stack guard.
- **`Event`, `Node` and every value stored in an array have no owning field.**
  An owning field makes the type move-only (TYPE-046) and an arena `get`
  returns a *copy*, so a node holding a `string` cannot be read back at all.
  Text lives in a side pool addressed by offset and length.
- **No dependencies** (PA-005). Not the compiler's `src/`, not its `lib/`, not
  `nregex`, not `ntime`. Adding one is a decision that has to be argued.
- **Never work around a compiler defect.** Record the reproduction, stop, and
  raise it. This is the compiler's own R6, and the reason applies here: a
  workaround buried in library code outlives the bug and is indefensible at
  verification time.

## The compiler constraints that shape everything

Full statement in `meta/specs/SAFETY.md` §1 and `../PLAYBOOK.md` §2. The ones
that bite hardest here:

- **A mutable module-level binding is refused** (D-211). All parser state is a
  value the caller holds. This is what makes the prototype's five format
  parsers unbuildable as written, not merely unfashionable.
- **Plain integer `+ - *` traps on overflow** (D-210).
- **There are no closures** (D-018), which is most of why the parser is *pull*
  rather than push.
- **Owning values are move-only** and **an arena `get` returns a copy**, so an
  arena element that owns anything cannot be read back.
- **`string_slice` allocates an owned copy** (D-186); `string_bytes` is the
  borrowed view. A parser that took a `string_slice` per token would allocate
  per token.
- **There is no map or hash container** anywhere in the language or the
  prelude. We scan, or we build one.
- `defer` does **not** run on a trap; `failsafe` is the only code guaranteed
  to run.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`end` (every range wants it), `in` (every byte source wants it), `error`,
`limit`, `any`, `buffer`, `raw`, `move`, `pick`, `fall`, `give`, `pass`,
`fail`, `relay`, `is`, `is_err`, `where`, `with`, `as`, `on`, `never`, `fails`,
`mod`, `unit`, `Self`, `Result`, `Optional`.

The substitutes this library uses, so they are used consistently: `hi` for an
upper bound, `src` for a byte origin, `sink` for a byte destination, `kind` for
a discriminant, `fault` for a parse failure value, `bound` for a limit, `depth`
for nesting, `tok` for a token.

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not.

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (PA-003). Until cycle 0.0.2
lands it, probes are run by hand — `meta/roadmap/0.0/0.0.0.md` §2 has the
command.

The compiler is at `../../nitpick`. Build it per its own `CLAUDE.md`. LLVM
20.1.2 exactly, pinned; `llvm-config --version` to check.

## Where things go

```
src/       the library, Nitpick only, layered per meta/specs/BUILD.md §6
tests/     probe, conformance, unit, roundtrip, rejection, fixtures, corpus
harness/   the Python build and test runner, until npkg can
tools/     the fuzzer, the corpus vendoring script
examples/  runnable demonstrations, built and run by the harness
docs/      user-facing documentation, written at cycle 1.0
meta/      specs, decisions, open questions, the roadmap, research
.internal/ gitignored scratch — never commit anything from here
```

## When you find something

- A **compiler defect**: record the reproduction, stop, raise it. Do not work
  around it.
- A **specification error**: fix the specification and record the decision, in
  the same commit as the code that revealed it.
- A **finding that is neither**: write it into the current subcycle's execution
  record. This project's execution records are load-bearing; the compiler's
  cross-cycle patterns exist only because one writer kept them.
