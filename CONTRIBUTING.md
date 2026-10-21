# Contributing

`nparse` is planned before it is written, and the plan is in the repository.
That is unusual and it is deliberate: the specifications catch design mistakes
that would otherwise be found by writing the wrong code twice — which, for
parsing in this ecosystem, has already happened five times.

## Before you write anything

Read, in this order:

1. `meta/specs/SAFETY.md` — the constraints
2. `meta/specs/README.md` — the index and the reading order
3. `meta/DECISIONS.md` — why things are the way they are
4. `meta/roadmap/ROADMAP.md`, then the current cycle's `README.md`

## The shape of a change

**Every change belongs to a subcycle.** The current cycle's `README.md` has the
checklist; a change that is not on it either goes on it or is a finding to be
recorded first.

**A specification change is a decision.** If your change requires the library to
behave differently from what `meta/specs/` says, the specification is amended
and a numbered decision recorded in `meta/DECISIONS.md`, **in the same commit**.
A settled decision's text is never rewritten — supersede it with a new one.

**Every change is green under the full harness.** `--only` is for iterating and
never for concluding; nothing is committed on the strength of a filtered run.

## The things that will surprise you

1. **A syntax error is not an error.** It is a `Fault` value in the success
   channel, and `pick` exhaustiveness is what forces the caller to handle it.
   The library declares two `error:` identities and **neither can be produced
   by any input**. If you find yourself adding a third, and the trigger is
   something a byte stream can cause, you have found a design mistake rather
   than a missing error.

2. **Arithmetic on input must not trap.** Plain integer overflow traps in
   Nitpick, so `acc = acc * 10 + d` is a remote crash on a long enough number.
   Range-check before the multiply, every time, and return a `Fault`. There is
   a gate for this and it is not negotiable.

3. **Nothing in a cell, node or event may own anything.** An arena refuses an
   owning element at `arena_make`, so a node holding a `string` cannot be stored
   at all; and an owning field costs a type `Copy`. Text is an offset and a
   length into a pool.

4. **The parser is pull, not push.** The caller asks for the next event. This
   is not a taste question: Nitpick has no closures, so a push parser's visitor
   would be a trait object plus hand-carried context at every call, and
   streaming would not compose.

And two that cycle 0.0.0's probes taught, which every later cycle meets:

5. **A size is measured, never summed.** A payload-free enum is a four-byte tag,
   so `Event` is 32 bytes where its fields once added up to 24. Every type whose
   size a rule asserts is measured by a probe: `Event` and `Node` by the probe's
   exit code (02 and 04), and `ParseError` by an assertion in probe 03, which exits
   19 at any other size.
6. **A compiler defect is recorded and waited for, never routed around.** The
   probes found two at compiler `7e91730` — a synchronous `Self->` method called
   through a generic bound did not link, and a view re-seated by a callee could
   outlive its bytes — and the compiler fixed both, DEF-253 and DEF-252, before
   the cycle's work began: probe 06 links and runs, and probe 08h is refused.
   Neither shape was re-spelled while it stood.

## Tests

- **Expectations live in the test file**, as markers, and assert on codes and
  exit codes — never on message text.
- **A negative test with no expectation is a failing test.**
- **Unexpected diagnostics fail a test as surely as missing ones.**
- **A conformance corpus is a gate, not a suggestion.** JSONTestSuite,
  toml-test and the yaml-test-suite subset are vendored, committed with their
  upstream commit recorded, and every case is judged. Hand-written cases test
  the rules the author understood.
- **The round trip is the oracle.** `print ∘ parse` must reach a fixed point
  after one normalisation, for every format, on every corpus case that parses.
- **Anything with a timing dimension runs forty times**, not once.
- **A red under stress is a stop sign, never a retry.**

## Compiler defects

You will find them; the library is written against a compiler that is itself
under construction. **Record the reproduction, stop, and raise it in the
compiler repository.** Do not work around it in library code: a workaround
buried here outlives the bug, is never removed, and is indefensible at
verification time.

## Style

Match the surrounding code. Public names carry their module's short prefix;
types are PascalCase; constants are SCREAMING_SNAKE. `meta/specs/BUILD.md` §7
lists the reserved words that read like ordinary names and the substitutes this
library uses instead — use those, so the tree is consistent.
