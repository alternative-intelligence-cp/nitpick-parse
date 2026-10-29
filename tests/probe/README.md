# `tests/probe/` — the language probes

Small programs that ask the compiler whether a shape `meta/specs/` depends on is
spellable, compilable and correct — written and measured by cycle 0.0.0
([`meta/roadmap/0.0/0.0.0.md`](../../meta/roadmap/0.0/0.0.0.md), whose §6 holds every
verdict), and kept as a regression suite for the language this library is built
on. **A probe is never deleted.** A compiler change that breaks one of these
shapes is caught here, not by a format failing mysteriously in a later cycle.

Every probe is a program: its own `main` and `failsafe`, importing nothing from
`src/`. Its `failsafe` names exactly the identities the compiler says can
reach it (`NITPICK-REACH-003`), with the arm codes of `PLAYBOOK.md` §3 item 8 and
the three the library adds — 97 `DivByZero`, 98 `DivOverflow`, 110 `StaleHandle`
(`meta/DECISIONS.md`, PA-109) — and every assertion's own code is below 91.

## The three kinds, one directory each

| directory | what a file there is | its header |
|---|---|---|
| `tests/probe/` | a program that compiles, links and runs; judged by its exit code at `-O0` and again through `opt -O2` | `// expect-exit: N`, and `// mem-cap-mib: N` where it runs under an address-space cap |
| [`refused/`](refused/) | a program the compiler must refuse with exactly the codes it names | `// expect-error: CODE` and `// expect-error-at: L:C` |
| `defect/` | the reproduction of a compiler defect, with its controls and a README saying what it blocks — none at the pin, so the directory is not made | the verdict it was written against, as a comment |

A probe's header is a hypothesis; the verdict is the table in `0.0.0.md` §6. A
size probe exits with the `#size_of` of its subject — `Event` (02), `Step` (03),
`Node` (04) — so that number cannot be transcribed wrongly; any other size it
reports is an assertion with its own exit code below 20 (02's `Span` and
`TextRef`, 03's `ParseError`).

## The two compiler defects these probes found, both fixed in the pin

Both were found at compiler `7e91730`, where this cycle was planned, and both
were fixed by the compiler before the cycle's work began, so each probe is an
ordinary one here:

- probe 06, `probe06_trait_bound.npk`, and its two controls,
  `probe06b_bound_by_value.npk` and `probe06c_concrete_pointer.npk` — a
  synchronous `Self->` method called through a generic bound, accepted by `npkc`
  and refused by `llc` at `7e91730`: the compiler's DEF-253, fixed by its landing
  118. At the pin it links and runs (PA-106). Since cycle 0.0.2 the harness's
  `probe` suite runs the three.
- probe 08h, [`refused/probe08h_view_reseated.npk`](refused/probe08h_view_reseated.npk) — a view
  re-seated by a callee, which read freed memory at `7e91730`: the compiler's DEF-252,
  refused from its landing 116, `NITPICK-BORROW-002` (PA-107).
