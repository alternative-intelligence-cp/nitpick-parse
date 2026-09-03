# Open questions

Everything that is not settled, each with a recommendation, so that nothing
lives only in a conversation. Three prefixes:

| Prefix | Whose |
|---|---|
| `O-x` | **ours** — a design question this project decides, at the cycle named |
| `O-N` | the **compiler's** — a gap in the language or its tooling that `nparse` needs closed, to be raised as a request |
| `Q-` | the **user's** — a question that wants an answer before the work it gates begins |

A question that gets answered moves to `DECISIONS.md` as a numbered decision and
is struck through here with the decision's number, **never deleted** — the
question is part of the record of how the answer was reached.

**No cycle in the plan is blocked on a question.** What remains open is open by
design: three measurements taken in the cycles that can take them, two questions
that wait for a consumer to ask, one gated on the compiler's tooling, and four
that are the compiler's rather than ours.

---

## Q — for the user

### Q-1 — the YAML subset boundary
`FORMATS.md` §4 draws the line where the security hazards are (anchors, aliases,
tags, directives) and where the semantics are undefined (merge keys), leaving
block and flow collections, all four scalar styles, comments, the core schema
and single documents.

**Recommendation: as stated**, with full YAML as post-1.0 cycle 1.1 where
anchors get an expansion budget as a first-class part of the design. Confirmed
at cycle 0.8 against the yaml-test-suite's actual tag distribution — if the
excluded constructs turn out to be a third of real-world YAML, the line moves
and the decision is amended rather than quietly stretched.

### Q-2 — XML, post-1.0
Out at 1.0 (PA-052) because its data model needs `Attribute` and mixed content,
which is a major version of the event vocabulary however it is scheduled.

**Recommendation: post-1.0 as cycle 1.2**, after full YAML, opening with its own
decision batch whose first item is the event-vocabulary extension. Deciding it
now would be deciding it without the two formats' worth of evidence that 0.8 and
1.1 produce.

### Q-3 — the arbitrary-precision accessors at 1.0
`doc_int256` and a `frac`-valued accessor cost little (the literal's text is
already retained under `ND_BIG`, PA-033) and serve the caller who parses a
financial document or a scientific dataset.

**Recommendation: yes, at 1.0** — `doc_int256` in cycle 0.4 with the rest of the
accessors, and a `frac64` accessor only if the exact-decimal case turns out to
have a consumer. The information is kept either way; what is at stake is one
function, not the representation.

### Q-4 — the dogfood consumer
The library's own examples are its first consumer and they are weak evidence: an
example is written by the person who wrote the API. A real program exercises it
honestly.

**Recommendation: a configuration-file linter**, at cycle 0.12, in `examples/`
in this repository so it moves with the API. It is the right shape because it
uses every layer — it reads TOML and JSON and YAML, it needs `Document`, it
needs *recovery* and multi-fault rendering (which nothing else in the plan
exercises hard), and it wants the path language. A transcoder would exercise the
event path instead; the linter is the better single choice and the transcoder is
already the `WRITER_MODEL.md` W-15 example.

---

## O-N — the compiler's

Each is a request to be raised in the compiler repository, not something this
project can fix. None blocks planning; one blocks a claim.

### O-N1 — `npkg` cannot build a library, and `[dependencies]` resolves to nothing
Measured at the compiler's 1.5.0 and recorded in `specs/BUILD.md` §1.
`npkg build` is the compiler's own bootstrap ladder; `target = "library"` is
accepted by the schema and read by nothing; the loader's dependency-root list is
created empty in `src/driver/pipeline.npk` and `rootlist_add` is called from
nowhere, so the dependency-root `use` form resolves against an empty set.

**Consequence:** `nparse` builds through its own Python harness (PA-003) and
every import is relative until this closes.
**Ask:** `npkg build` honouring `target = "library"`, and the driver populating
the resolver's roots from `[dependencies]`. Neither is on the compiler's 1.5 or
1.6 map, so this is a request, not a date.

### O-N2 — there is no stack-depth guard, and `stack-depth` obligations are 1.5.8
`VERIFICATION_REFERENCE.md` §365 lists `stack-depth` as an obligation kind
scheduled for 1.5.8; nothing exists today. A recursive descent on
`[[[[[[[[…` is therefore an **uncontrolled** fault rather than a controlled
stop, which is the one failure mode this ecosystem exists to make impossible.

**Consequence:** `nparse` forbids native recursion on any input-controlled path
(PA-022) and holds the rule with a **grep** — `check_no_recursion`
(`TESTING.md` §3) — rather than with a proof.
**Ask:** nothing new; 1.5.8 as planned. Recorded because when it lands, that
check becomes a discharged obligation and the exceptions table becomes provably
empty, which is a real upgrade to the library's central safety claim
(`VERIFICATION.md` P-10).

### O-N3 — there is no map or hash container in the language or the prelude
Measured: `TYPE_REFERENCE.md` lists no map type, the prelude declares none, and
D-041 explicitly returned the collection keywords to userland.

**Consequence:** `Document` lookup is a linear scan with an explicit opt-in
index (`VALUE_MODEL.md` §5), and `SmallMap<K,V>` is ours (PA-004).
**Ask:** none — this is a deliberate language decision and the library's answer
is fine. Recorded only so that the question "why is there no hash map here" has
a written answer, because it is asked every time somebody meets the value model.

### O-N4 — `arena.get` returning a copy is load-bearing and easy to miss
Not a defect — D-152 argues it correctly (a borrow-returning `get` would be a
returned borrow, which D-004 refuses everywhere). But its interaction with
TYPE-046 is the single most consequential language fact for this library's value
model (PA-030), and it is stated in `MEMORY_REFERENCE.md` §4.2 in a sentence
about mutation rather than as a constraint on element types.

**Ask:** a sentence in `MEMORY_REFERENCE.md` §4.2 saying plainly that **an arena
element type may not own anything**, because `get` copies and a copy of an owner
is refused. It would have saved this library a design iteration and it will save
the next one.

---

## O-x — ours

### Safety and limits

- **O-P1 — the duplicate-key default.** Settled in `VALUE_MODEL.md` D-14 and
  PA-032 as **a fault by default with a policy**, on the parser-differential
  argument. It stays listed until **cycle 0.4 confirms it against the corpora** —
  specifically that JSONTestSuite has no `y_` case with a duplicate key that our
  default would now reject. If it does, the default for JSON changes and the
  decision is amended.
- **O-P2 — `NPARSE_MAX_SCALAR` (16 MiB).** **Open by design:** a guess, not a
  measurement. Confirmed at cycle 0.3 against JSONTestSuite and a realistic
  large-document sample, and the number chosen is recorded with the
  measurement.

### Scanning and diagnostics

- **O-P3 — whether `scan_line_col` should memoise.** A document with a thousand
  faults would scan from the start a thousand times, which is quadratic.
  **Open by design:** a *measurement*, taken at cycle 0.9 when recovery makes
  many-fault documents real. The answer is either "leave it" or "build a
  line-start index once, on the first diagnostic".
- **O-P10 — whether `fault_render` should render several faults with shared
  context.** The same quadratic as O-P3 seen from the caller's side. **Open by
  design:** measured at cycle 0.9, and the two share one answer.
- **O-P7 — the third-party fault-code mechanism.** `FormatSpecific(uint16)`
  versus a reserved band in the closed enum. **Recommendation:
  `FormatSpecific`**, because a reserved band in a closed enum is a band
  somebody eventually collides in. Decided at cycle 0.9 with the diagnostic
  work.

### The event contract

- **O-P5 — whether `Comment` should carry its position relative to the
  construct it annotates** (leading, trailing, own-line). A formatter needs it;
  a data consumer does not. **Recommendation: not at 1.0** — `keep_comments`
  gives the span, and a formatter can derive the relation from spans it already
  has. Revisit if a formatter is written against the library.
- **O-P6 — incremental feeding.** At 1.0 a parser is constructed over a
  complete `uint8[]`; a chunked parser must suspend mid-token, which turns every
  scanning function into a resumable state machine. **Open by design:** a
  *measurement*, taken at cycle 0.10, and the **contract does not depend on the
  answer** — a chunked parser produces the same events, so this is an
  implementation question rather than a design one.

### The document model

- **O-P8 — whether the pool should intern repeated keys.** A configuration file
  with a thousand tables repeats every key name. **Open by design:** a
  *measurement*, taken at cycle 0.11 against a realistic corpus. The answer is
  either "leave it" or "intern keys only, in the side index the builder already
  has for large maps".
- **O-P9 — whether `Document` should be mutable.** At 1.0 it is built once and
  read; there is no `doc_set`. A configuration *editor* would want mutation and
  order preservation together, which is arguably the CST library of
  `PLUGIN_MODEL.md` §7 rather than this one. **Recommendation: read-only at
  1.0**, revisited when a consumer asks — cycle 0.12's linter is the first that
  can.

### The formats and the writers

- **O-P4 — the datetime overlap with `ntime`.** TOML has four date-time types;
  `nparse` scans and classifies them and interprets nothing (`FORMATS.md` R-9).
  When dependency resolution lands (O-N1) and `ntime` exists, the question is
  whether `nparse` should gain an optional accessor returning an `ntime` value.
  **Recommendation: no** — `nparse` keeps the text and the *caller* converts,
  because a parsing library that grew a date library inside it is how the
  duplication this library exists to end starts again.
- **O-P11 — the YAML subset boundary.** See Q-1.
- **O-P12 — whether YAML's writer should emit flow style for short
  collections.** Block everywhere is simpler, deterministic and ugly for
  `[1, 2, 3]`. **Recommendation:** block everywhere in the *canonical* form,
  flow as an `EmitOpts` option — the canonical form has one answer and the
  pretty printer can have taste. Decided at cycle 0.8.
