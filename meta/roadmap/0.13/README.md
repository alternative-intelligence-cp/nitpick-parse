# Cycle 0.13 — Hardening

**The fuzz sweep, the corpora completed, `check_no_recursion` proven empty, and
the verification obligations reconciled and handed forward.**

## Decisions in

PA-083, and `specs/VERIFICATION.md` in full.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.13.0 | **The fuzz sweep** — all four formats, all five invariants | a hundred million inputs, clean |
| 0.13.1 | **The adversarial corpus** — the shapes designed to break PA-012 and PA-022 | each one a permanent fixture |
| 0.13.2 | **The corpora completed** — every count pinned, every `i_` verdict recorded | the gates final |
| 0.13.3 | **The checks proven** — `check_no_recursion`'s exceptions empty | the depth claim held by a check with nothing excused |
| 0.13.4 | **Verification reconciliation** — the obligation list against the code | `meta/OBLIGATIONS.md` |
| 0.13.5 | **The audit** — every spec rule read against its implementation | a findings list, specs corrected |
| 0.13.6 | **Close** | `done/0.13/`, `1.0.0.md` written |

## Checklist

### 0.13.0 — the fuzz sweep
- [ ] `tools/fuzz.py` over all four formats plus the trivial fifth, with the five invariants from `specs/TESTING.md` §7
- [ ] **invariant 1 — it never traps — is the one that matters**: the process exits with the program's own code, never through `failsafe` with `IntOverflow`, `OutOfBounds` or `Unreachable`
- [ ] a hundred million inputs across the five, clean
- [ ] every accepted fuzz input round-tripped, because that is where the interesting failures are
- [ ] anything found becomes a permanent case in `tests/fixtures/` with its fault recorded in the marker

### 0.13.1 — the adversarial corpus
- [ ] the shapes designed to break the two central rules, each a committed fixture: a 5000-digit integer; `1e999999999`; fifty thousand `[`; a 100 MB string; a `\u` escape at every boundary; a surrogate pair split across a chunk boundary; a map with a million keys; a document that is one unterminated string
- [ ] each asserted to produce a **`Fault`**, not a trap, not a hang, not an `error:`
- [ ] the 100 MB and 50 000-deep cases run under `opt -O2` too (B-3), because an optimiser reordering a guard is exactly the defect this corpus exists to catch

### 0.13.2 — the corpora completed
- [ ] every corpus's pass count final and pinned
- [ ] JSONTestSuite's `i_` verdicts all recorded
- [ ] the yaml-test-suite filter list complete, with every excluded case producing `Unsupported`
- [ ] `check_corpus_provenance` green over all four

### 0.13.3 — the checks proven
- [ ] `check_no_recursion`'s exceptions table **empty**, and the check green over the whole tree (0.0.3's P-20)
- [ ] `check_no_raw_accumulate` green with no exceptions
- [ ] `check_error_budget` reporting exactly two
- [ ] `check_no_owning_fields` covering every value in a `Vec` or an arena
- [ ] every tree check in `specs/TESTING.md` §3 live, with none reporting a pending row

### 0.13.4 — verification reconciliation
- [ ] `specs/VERIFICATION.md`'s obligation list read against the code, entry by entry
- [ ] every obligation the code generates that the list does not name, added
- [ ] every obligation the list names that the code does not generate, removed or scheduled
- [ ] the `requires`/`ensures` comments checked to be **syntactically** what they will be, by pasting one into a scratch file and confirming the compiler's rung refuses it **by name** rather than parsing it as something else
- [ ] the property tests standing in for each, present and green
- [ ] the whole list handed forward as `meta/OBLIGATIONS.md` (P-13), ready for the compiler's verified build

### 0.13.5 — the audit
- [ ] every specification document read against the code that implements it
- [ ] every numbered rule either implemented, refused with a reason, or struck by a decision
- [ ] the tree checks' coverage reviewed: **is there a document nothing diffs against?**
- [ ] `check_specs_current`'s backlog drained

## Gate

A hundred million fuzz inputs clean, `check_no_recursion` with an empty
exceptions table, and an obligation list that is true.

## Watch for

- **The audit is the cycle's most valuable part and the easiest to shorten.**
  The compiler's cycle 0.6 found every one of its holes this way and none of
  them by a test.
- **A specification rule with no implementation and no refusal is the failure
  this cycle exists to find** — the dormant-rule pattern, which the compiler
  found three times.
- **A red under the fuzzer is a stop sign, never a retry** (V-11's discipline
  applied). Every timing- or input-shaped defect looks like flakiness first.
