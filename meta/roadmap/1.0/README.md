# Cycle 1.0 — Release

**Documentation, the API freeze, the `failsafe` arm contract, and the version
policy.**

## Decisions in

PA-009 — settled in the founding batch. This cycle **publishes** it; it does not
decide it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 1.0.0 | **The API freeze** — the public surface enumerated, reviewed name by name | `src/lib.npk` as the contract |
| 1.0.1 | **The `failsafe` contract** — the per-import arm list, published | a consumer knows exactly what importing costs |
| 1.0.2 | **The guide** — `docs/` | a person can build against it from the documentation alone |
| 1.0.3 | **Examples** — one per format, plus the architectural ones | every example built and run by the harness |
| 1.0.4 | **Versioning** — PA-009 published | the policy where a consumer will read it |
| 1.0.5 | **Close** | `done/1.0/`, the post-1.0 map reviewed |

## Checklist

### 1.0.0 — the API freeze
- [ ] `src/lib.npk` lists every public name, one per line, grouped by module
- [ ] each reviewed: is it needed, is it named right, does it belong at this layer?
- [ ] anything not needed removed **now** — removing a public name after 1.0 is a major version
- [ ] a conformance test importing the umbrella and touching every name, so a removal breaks a test rather than a user
- [ ] the closed enums (`EventKind`, `ScalarKind`, `NodeKind`, `FaultCode`) reviewed one variant at a time, because **adding one later is a major version** (PA-009)

### 1.0.1 — the `failsafe` contract
- [ ] the per-import arm list generated (`specs/SAFETY.md` S-7) and published in `docs/`
- [ ] `check_failsafe_arms` proving the published list is what a program actually owes
- [ ] **the headline stated once, prominently**: `nparse` declares two error
      identities, `EParseState` and `EParseEncode`, and **no input can produce
      either** — every condition a byte stream can cause is a `Fault` value the
      compiler makes you handle
- [ ] the modules that declare **no** errors named explicitly (`scan`, `event`,
      `diag`), because a consumer importing only those owes nothing

### 1.0.2 — the guide
- [ ] getting started: parse a JSON file and read a value, in under twenty lines
- [ ] the model: pull events, the `Fault` arm, why a syntax error is not an
      error, and what that costs you (one `pick` arm) versus what it buys (a bad
      byte cannot stop your program)
- [ ] the streaming path and the tree path, with the 0.10 measurements saying
      which to reach for
- [ ] writing a plugin: the `Format` trait, the eight obligations,
      `plugin_conform`, and the trivial format in `tests/` as the worked example
- [ ] every format's subset and version, from `specs/FORMATS.md`
- [ ] **a page on what `nparse` deliberately does not do, and why**: no XML at
      1.0, no full YAML, no CST or incremental reparse, no query language, no
      date interpretation, no file reading, no schema validation

### 1.0.3 — examples
- [ ] one per format, minimal
- [ ] the transcode loop (`WRITER_MODEL.md` W-15)
- [ ] a custom `Format` plugin
- [ ] a streaming consumer over JSON Lines
- [ ] the 0.12 linter
- [ ] every example built **and run** by the harness, so a broken example is a red run

### 1.0.4 — versioning
- [ ] PA-009's policy written into `docs/` and the release notes
- [ ] **the three major-version triggers stated prominently**: a new `error:`
      identity, a new variant in any closed enum, and any removal — the first
      two being rules no other language's library has to have
- [ ] the current counts published beside them (two identities; nine
      `EventKind`s; nine `ScalarKind`s), so a consumer can see the budget rather
      than infer it

## Gate

A person who has not seen the code can parse a document, handle a fault, walk a
tree and write a plugin from `docs/` alone — and every example is green in the
harness.

## After

The post-1.0 map in `ROADMAP.md`: full YAML with an anchor expansion budget
(1.1), XML with its event-vocabulary extension (1.2), the `nitpick-cst` question
(1.3), and the verified build once `npkg verify` reaches libraries (1.4).
