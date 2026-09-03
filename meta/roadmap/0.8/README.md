# Cycle 0.8 — YAML

**`src/format/yaml.npk` and `src/emit/yaml.npk`: YAML 1.2 core schema, the
subset PA-051 states.** The largest specification in the set, implemented
deliberately partially, with every exclusion named rather than silent.

## Why a subset, and why that subset

`specs/FORMATS.md` §4 has the construct list; the reasoning is worth repeating
because it is the cycle's whole shape:

- **anchors and aliases are the billion-laughs amplification vector.** A bounded
  implementation needs an expansion budget, a cycle detector and size accounting
  that the rest of the library does not have — a design, not a feature.
- **merge keys** are a convention YAML 1.2 does not define.
- **tags** beyond the core schema are a type system.

**Shipping a "YAML parser" that silently ignored anchors would be worse than one
that refuses them by name**, which is why `Unsupported` is a distinct
`FaultCode` from `UnexpectedByte` (F-5) and why the renderer names the
construct.

Full YAML is post-1.0 cycle 1.1, with anchors carrying an expansion budget as a
first-class part of the design.

## Decisions in

PA-050, PA-051, PA-053, PA-060. All settled.

**Open questions to settle:** Q-1 / O-P11 (the subset boundary) — **confirmed
here against the yaml-test-suite's actual tag distribution.** If the excluded
constructs turn out to be a third of real-world YAML, the line moves and the
decision is amended rather than quietly stretched. O-P12 (flow style in the
writer) is decided here too.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.8.0 | **The corpus and the filter** — yaml-test-suite vendored, the exclusion list | every excluded case producing `Unsupported`, not skipped |
| 0.8.1 | **Indentation** — the block context machine | the indentation rules, tested at every boundary |
| 0.8.2 | **Scalars** — plain, single, double, literal `\|`, folded `>` | chomping and indentation indicators |
| 0.8.3 | **Collections** — block and flow, mappings and sequences | nesting and the flow/block transitions |
| 0.8.4 | **Core-schema resolution** — the plain-scalar traps | `no`/`on`/`off` are strings |
| 0.8.5 | **The writer** — the canonical form | the round trip green over the filtered corpus |
| 0.8.6 | **Close** | `done/0.8/`, `0.9.0.md` written |

## Checklist

### 0.8.0 — the corpus and the filter
- [ ] yaml-test-suite vendored with `PROVENANCE.md`
- [ ] **the filter is a committed list of case identifiers with the excluded construct named per case** (V-11) — not a regex, not a count
- [ ] **every excluded case must produce `Fault(Unsupported)`**, so the exclusions are *tested* rather than skipped — this is the difference between a stated subset and an unstated gap
- [ ] the suite's expected event streams compared mechanically against ours — **the largest single reason to have adopted this event vocabulary** rather than inventing one
- [ ] Q-1 confirmed: the actual proportion of the suite touching excluded constructs, measured and recorded

### 0.8.1 — indentation
- [ ] the block context machine: indentation levels, the `Vec<Frame>` carrying them, and the depth bound
- [ ] `Fault(BadIndent)` on inconsistent indentation, with a span
- [ ] tabs refused where YAML refuses them, and the message saying so
- [ ] the boundary cases: a document at column 0, a sequence at the same indent as its key, a nested mapping under a sequence entry

### 0.8.2 — scalars
- [ ] plain scalars and their termination rules (the hardest part of YAML scanning)
- [ ] single-quoted with `''`, double-quoted with the full escape set through `arith.npk`
- [ ] literal `|` and folded `>` with **both** chomping indicators (`-`, `+`) and explicit indentation indicators
- [ ] `NPARSE_MAX_SCALAR` enforced on the decoded length
- [ ] multi-line folding rules asserted case by case from the suite

### 0.8.3 — collections
- [ ] block mappings and block sequences
- [ ] flow mappings `{}` and flow sequences `[]`, including nesting inside block context
- [ ] `---` and `...` markers with **exactly one document**; a second document is `Fault(Unsupported)`
- [ ] complex mapping keys `? key` refused as `Unsupported`

### 0.8.4 — core-schema resolution
- [ ] the core schema exactly: `null`, `true`/`false`, integers, floats, strings
- [ ] **the traps, each with a test** (R-15): `no`/`on`/`off`/`yes` are **strings** (the Norway problem — that is YAML 1.1 behaviour and we are 1.2); `07` is a base-10 integer with a leading zero, not octal; `0o7` is octal; a sexagesimal-looking value is a string
- [ ] a test asserting we do **not** implement YAML 1.1 resolution, because that is the divergence a user is most likely to be surprised by

### 0.8.5 — the writer
- [ ] the canonical form: block style, two-space indentation, plain scalars where resolution is unambiguous and single-quoted otherwise, no document markers unless the input had them
- [ ] O-P12 decided: **block everywhere in the canonical form**, flow as an `EmitOpts` option — the canonical form has one answer and the pretty printer can have taste
- [ ] a scalar that would resolve to the wrong type if written plain is quoted — the writer's one non-obvious obligation, and the one that makes the round trip pass
- [ ] the round trip green over the filtered corpus

## Gate

The filtered yaml-test-suite green with an exact count, **every excluded case
producing `Unsupported`**, and the round trip green over everything that parses.

## Watch for

- **Plain-scalar termination is where YAML parsers go wrong**, and it interacts
  with flow context, indentation and comments all at once. Work from the suite's
  cases, not from the specification's productions.
- **The writer's quoting obligation is subtle.** A string `"no"` written plain
  reads back as a string under the core schema — but a string `"true"` written
  plain reads back as a boolean. The round trip is what catches it, which is why
  the oracle exists before this cycle.
- **Resist widening the subset mid-cycle.** If a case looks like it needs
  anchors, it needs cycle 1.1. Amend the decision or refuse the case; do not
  add a half-implementation, which is precisely what PA-051 exists to prevent.
