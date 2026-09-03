# `nparse` specifications

This directory is the **authority on what `nparse` does**. Code that disagrees
with a document here is a defect in the code; a document that turns out to be
wrong is amended by a decision recorded in
[`../DECISIONS.md`](../DECISIONS.md), never by editing the text and moving on.

That discipline is borrowed, deliberately, from the compiler repository, where
the cycle notes record the same finding over and over: **the compiler and the
thing that describes it have to be diffed, because reading either alone never
reveals the gap.** A specification nothing is held to is decoration.

## Reading order

Read the first two before proposing anything. `SAFETY.md` contains the two
rules that shape this library more than every other decision combined — a
syntax error is a *value*, and arithmetic on input must not trap — and most
proposals that look reasonable in the abstract die on one of them.

| # | Document | What it settles |
|---|---|---|
| 1 | [`SAFETY.md`](SAFETY.md) | the error budget, the no-trap rule, the depth rule, the resource discipline — **the constraints, and where they come from** |
| 2 | [`BUILD.md`](BUILD.md) | how this is built and tested today, and the module, layering and import conventions |
| 3 | [`SCAN_MODEL.md`](SCAN_MODEL.md) | the cursor, spans, UTF-8, escapes, and number scanning that cannot trap |
| 4 | [`EVENT_MODEL.md`](EVENT_MODEL.md) | the event vocabulary, `Step`, the pull driver, `TextRef`, the depth stack |
| 5 | [`PLUGIN_MODEL.md`](PLUGIN_MODEL.md) | what a plugin is, what it owes, and how a third party writes one |
| 6 | [`VALUE_MODEL.md`](VALUE_MODEL.md) | `Document`, nodes, the string pool, ordered maps, duplicates, numbers |
| 7 | [`DIAGNOSTIC_MODEL.md`](DIAGNOSTIC_MODEL.md) | `ParseError`, the code enum, spans, rendering, recovery |
| 8 | [`FORMATS.md`](FORMATS.md) | which formats, which version of each, which subset, and the conformance corpus that gates it |
| 9 | [`WRITER_MODEL.md`](WRITER_MODEL.md) | the writers, canonical forms, and the round-trip properties |
| 10 | [`TESTING.md`](TESTING.md) | the harness, the corpora, the round-trip oracle, differential testing, fuzzing |
| 11 | [`VERIFICATION.md`](VERIFICATION.md) | the proof obligations this library carries into the compiler's cycle 1.5 |
| 12 | [`GLOSSARY.md`](GLOSSARY.md) | the words, used one way each |

## What is normative, and what is not

- A **rule** stated in these documents is normative. Rules read as statements of
  fact about the library ("an `Event` has no owning field"), not as intentions.
- A **rationale** paragraph explains why, and carries no obligation of its own.
- A **decision reference** — `PA-nnn` — points at
  [`../DECISIONS.md`](../DECISIONS.md), which holds the argument, the
  alternatives considered, and the date. `D-nnn` points at the **compiler's**
  `meta/specs/DECISIONS.md`; those are language decisions and are not ours to
  amend.
- An **open item** is listed at the end of the document that owns it, and is
  mirrored in [`../OPEN_QUESTIONS.md`](../OPEN_QUESTIONS.md) with a
  recommendation. A question that lives only in a conversation evaporates.

## The language, in one paragraph, for a reader arriving from C

Nitpick has no exceptions and no unhandled errors: every function returns
`Result<T>` except `main` and `failsafe`. There is no garbage collector; the
default regime is static ownership with destruction at scope exit, owning values
are move-only, and borrows are second class — they pass down the call stack and
never up. **Plain integer overflow traps.** There are no closures. There are no
mutable module-level bindings. `defer` runs on every normal exit path and **not**
on a trap. Anything uncaught routes through a mandatory `failsafe` handler,
which is the last code that runs in a process that has decided to stop. Read the
compiler's `meta/specs/` for the full statement; the pieces that bite hardest
here are enumerated in [`SAFETY.md`](SAFETY.md) §1.

## The one-paragraph summary of this library

Formats are plugins over a shared **pull event stream**. A `Format`
implementation reads bytes the caller owns and answers `Ev`, `Fault` or `Done`;
a small tree builder over that stream produces a `Document` for callers who want
one. Scalar text is a reference into the input, so nothing proportional to the
input is copied. A syntax error is a value the caller must handle, never an
error identity — **no input can produce one of the two identities this library
declares**.
