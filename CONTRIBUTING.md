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

## The four things that will surprise you

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

3. **Nothing in a cell, node or event may own anything.** An owning field makes
   the type move-only, and an arena `get` returns a copy — so a node holding a
   `string` cannot be read back at all. Text is an offset and a length into a
   pool.

4. **The parser is pull, not push.** The caller asks for the next event. This
   is not a taste question: Nitpick has no closures, so a push parser's visitor
   would be a trait object plus hand-carried context at every call, and
   streaming would not compose.

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
