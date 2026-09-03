# nparse

A multi-format parsing library for **[Nitpick](https://github.com/alternative-intelligence-cp/nitpick)** —
the safety-critical systems language. One event stream, one document model, one
set of scanning primitives, and formats as plugins over them. No dependencies,
no libc, and **no syscall of any kind**: it is pure computation over bytes the
caller hands it.

> **Status: planning.** No code yet. The specification set is being written in
> [`meta/specs/`](meta/specs/) and the plan in [`meta/roadmap/`](meta/roadmap/),
> in the same order and by the same discipline the compiler used — specs first,
> then a cycle map, then execution-grade subcycles, then code. The compiler
> itself is at cycle 1.5 (verification); this library is planned now so that
> implementation can start the day the language stops moving.

---

## Why this library exists

Because in the prototype era **every library wrote its own parser**, and the
duplication is measurable. `njson`, `ntoml`, `nyaml`, `ncsv` and `nxml` each
carried their own token-kind table, their own lexer, their own node table with
its own hard-coded capacity, their own integer-tagged value model with manual
bit packing, and their own mutable global error string. Five copies of one
design, each with its own bugs.

None of that architecture survives contact with the current language anyway:
**a mutable module-level binding is refused** since the compiler's 1.4.2b
(D-211), and every one of those parsers kept its entire state in exactly that.
So the choice is not "port or rewrite" — it is "rewrite, once, properly, and
share it".

## What makes it different

**A syntax error is a value, not an error.** This is the headline. In Nitpick
every public `error:` a library declares becomes a mandatory `pick` arm in
every consuming program's `failsafe`, and an unhandled one stops the process.
For a library whose entire job is reading input somebody else controls, routing
malformed input through that channel would mean a bad byte can stop a program.
So it does not: `parse_next` returns a `Step` — `Ev`, `Fault(ParseError)` or
`Done` — and `pick` exhaustiveness makes the caller handle the fault. **No
input, however hostile, can produce an error identity.** The two the library
declares can only fire on programmer misuse.

**Parsing a number cannot stop your program.** Plain integer overflow *traps*
in Nitpick (D-210), so the ordinary `acc = acc * 10 + d` accumulator crashes the
process on `99999999999999999999999` — an input anyone can type. Every
accumulation in `nparse` is range-checked *before* the multiply, and the
overflow answer is a `Fault`, not a trap. There is a test for exactly this and
it is one of the library's gates.

**Recursion cannot blow the stack**, because there is none. Nitpick has no
stack-depth guard, and `[[[[[…` is the oldest trick there is. Both the parser
and the tree builder use an explicit stack with a stated, tested bound.

**Zero-copy by construction.** An `Event` is a plain 24-byte value with no
owning field; scalar text is a `TextRef` into the caller's input, or into the
parser's scratch when an escape had to be decoded. Parsing a 1 GB file
allocates nothing proportional to the file.

**The round trip is the test.** Every format that reads also writes, and the
oracle is `print ∘ parse` reaching a fixed point after one normalisation — the
strongest statement a parser can make about itself, and one that costs a
printer you wanted anyway.

---

## What it will provide

| Layer | Contents |
|---|---|
| **scan** | a cursor over `uint8[]`, byte offsets and on-demand line/column, UTF-8 validation, escape decoding, and number scanning that cannot trap |
| **event** | the format-neutral event vocabulary, the `Format` trait, the pull driver, the depth stack |
| **doc** | `Document` — an arena-backed tree of POD nodes with a side string pool, insertion-ordered maps, and a duplicate-key policy |
| **diag** | `ParseError`: a closed code enum, a span, an expected set, and a renderer |
| **format** | JSON (RFC 8259), TOML (1.0.0), CSV (RFC 4180 + dialects), and a precisely defined YAML subset |
| **emit** | a canonical writer per format, and the round-trip properties they satisfy |

A **plugin is a `Format` trait implementation** and nothing else. There is no
registry, no dynamic loading (Nitpick has no `dlopen` and no in-process FFI),
and no macro. A third-party format implements one trait and every consumer of
the event stream — the tree builder, the query API, the writers, the fuzzer —
works on it unchanged.

---

## Layout

```
src/          # THE LIBRARY — Nitpick source only
  core/       #   Vec, Bytes, SmallMap, and the one file of named limits
  scan/       #   cursor, spans, UTF-8, escapes, non-trapping number scanning
  event/      #   the event vocabulary, the Format trait, the depth stack
  doc/        #   the Document tree and the query API
  diag/       #   ParseError, codes, rendering
  format/     #   json, toml, csv, yaml — the shipped plugins
  emit/       #   the writers
tests/        # probe, conformance, unit, roundtrip, rejection, fixtures, corpus
examples/     # runnable demonstrations, built AND run by the harness
harness/      # the Python build and test runner, until `npkg` can build a library
tools/        # the fuzzer and the corpus vendoring script
meta/specs/   # the design authority
meta/roadmap/ # the plan, in numbered cycles
docs/         # user-facing documentation, written at 1.0
```

## Specification

[`meta/specs/`](meta/specs/) is the authority on behaviour, and
[`meta/DECISIONS.md`](meta/DECISIONS.md) records every settled design decision
with its reasoning — start there when something looks unusual, because it is
recorded why.

## Plan

[`meta/roadmap/ROADMAP.md`](meta/roadmap/ROADMAP.md) is the cycle map. A cycle is
a folder, a subcycle is a file inside it, and a finished cycle moves to
`meta/roadmap/done/`.

## Requirements

The Nitpick compiler and LLVM 20.1.2 — the same toolchain the compiler pins.
Nothing else, at build time or at run time. `nparse` makes no syscall, so
unlike most of the ecosystem it is not tied to Linux or to x86-64.

## Licence

Apache 2.0. See [`LICENSE`](LICENSE).
