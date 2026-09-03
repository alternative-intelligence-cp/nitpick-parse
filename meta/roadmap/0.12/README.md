# Cycle 0.12 — The dogfood consumer

**A configuration linter in `examples/`, written against the library as a
user.**

## Why a cycle

Because an example written by the person who wrote the API is weak evidence: it
demonstrates the features the author was thinking about. A program with a
purpose finds what is missing, what is awkward, and what is wrong — and it finds
it before a 1.0 that would have to keep it.

This is Q-4's answer, in this repository rather than a separate one, so the
program moves with the API and a breaking change breaks it in the same commit
rather than six months later.

## What to build, and why this one

A **configuration linter**: read a file in any of the four formats, report every
problem in it with a span and a caret, check it against a small set of
structural rules (required keys, unexpected keys, type expectations), and exit
non-zero if anything failed.

It is the right shape because it uses the layers nothing else exercises hard:

| Feature | Exercises |
|---|---|
| four formats from one code path | `dyn Format` (PA-071) and `builtin_open` |
| **every** problem, not the first | recovery, `max_errors`, multi-fault rendering (0.9) |
| spans and carets in real output | `fault_render`, and the codepoint-caret limitation (F-16) meeting real text |
| structural rules over a tree | `Document`, `doc_path`, `doc_find`, the accessors |
| a large file | the `Document` path's allocation, measured in anger |
| a malformed file, deliberately | the `Fault` arm as a caller experiences it |

A transcoder would exercise the event path instead, and it is already the
`WRITER_MODEL.md` W-15 example; the linter is the better single choice.

## Decisions in

PA-009's "the API has survived cycle 0.12's application". Settled.

**Open questions to settle:** the ones this cycle settles arrive from the
program rather than being listed in advance — that is the point of it. **O-P9**
(whether `Document` should be mutable) is the one most likely to be asked, since
a linter that could *fix* a file would want it, and 0.12.1's triage is where it
gets an answer with evidence behind it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.12.0 | **The program** — written straight through, recording every friction | a working linter, and a numbered findings list |
| 0.12.1 | **Triage** — every finding a defect, a gap or an accepted cost | a decision per finding |
| 0.12.2 | **The fixes** — the defects, and the gaps that survive triage | the library changed, goldens re-recorded only where intended |
| 0.12.3 | **Close** | `done/0.12/`, `0.13.0.md` written |

## Checklist

### 0.12.0 — the program
- [ ] written **without changing the library**, so every friction is recorded rather than smoothed over as it appears
- [ ] every awkwardness written down as it is met, numbered, with the line of code that caused it
- [ ] all four formats through one code path
- [ ] recovery on, reporting every problem in a deliberately broken file of each format
- [ ] a large real configuration tree linted, with time and memory noted
- [ ] built **and run** by the harness, so a broken example is a red run

### 0.12.1 — triage
- [ ] every finding classified: **defect** (the library is wrong), **gap** (a consumer reasonably needs something absent), or **cost** (the library is right and this is what the design costs)
- [ ] **every `cost` written into the documentation**, because an accepted cost nobody warned about is a defect in the documentation
- [ ] every `gap` sized, and either scheduled into 0.13 or recorded as post-1.0
- [ ] O-P9 revisited with evidence: did the linter want to write a file back?

### 0.12.2 — the fixes
- [ ] the defects fixed, each with a regression test
- [ ] the scheduled gaps closed
- [ ] goldens re-recorded **only** where a change was intended, and a re-record reviewed as a diff
- [ ] `check_error_budget` still reporting two — a consumer's convenience is not a reason for a third identity

## Gate

A configuration linter a person would actually use, and a triaged findings list
with a decision per entry.

## Watch for

- **The temptation to fix as you write.** The value of this cycle is the
  *record* of what was awkward; a friction smoothed over in the moment is a
  friction the next user meets too.
- **"It needs a feature" is usually "the example needs a helper".** A gap is
  only a gap if it cannot be written in the application in a reasonable number
  of lines.
- **Watch the `Fault` arm specifically.** This is the first time somebody who
  did not design PA-008 has to write one. If it is annoying, that is the single
  most important finding this cycle can produce, because it is the library's
  central design decision meeting its first real user.
