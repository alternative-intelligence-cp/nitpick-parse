# Cycle 0.10 — Streaming and large inputs

**The measurement that turns `specs/EVENT_MODEL.md` E-25 from a claim into a
number**, and the answer to O-P6.

## Why a cycle rather than a checklist item

Because "nothing proportional to the input is copied" is the property that
justifies the whole `TextRef` design (PA-014, PA-021), and a property nobody
measures is a property nobody has. And because O-P6 — whether a genuinely
incremental `feed(bytes)` is needed — should be answered by a measurement rather
than by a guess, and this is where the measurement exists.

## Decisions in

PA-006, PA-014, PA-021. All settled.

**Open questions to settle:** O-P6 (incremental feeding). **The contract does
not depend on the answer** — a chunked parser produces the same events — so this
is an implementation question, and the measurement decides it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.10.0 | **The 1 GB measurement** — all four formats, allocation profiled | a number, per format |
| 0.10.1 | **Constant-allocation proof** — the event path asserted | allocation independent of input size |
| 0.10.2 | **Record-oriented streaming** — JSON Lines and CSV | a 10 GB file through a fixed window |
| 0.10.3 | **O-P6 answered** — with the measurement | a decision, either way |
| 0.10.4 | **Close** | `done/0.10/`, `0.11.0.md` written |

## Checklist

### 0.10.0 — the 1 GB measurement
- [ ] a 1 GB document generated per format (a generator in `tools/`, deterministic, not committed)
- [ ] parsed through the **event path**, with peak allocation and wall time recorded
- [ ] parsed into a **`Document`**, with the same recorded — the contrast is the point, and it is what tells a caller which layer to use
- [ ] the numbers written into `meta/bench/` and into this cycle's record

### 0.10.1 — constant-allocation proof
- [ ] the event path's allocation asserted **constant in the input size**: parse 1 MB, 100 MB and 1 GB, and require peak allocation within a small constant of each other
- [ ] the scratch's high-water mark bounded by `NPARSE_MAX_SCALAR` regardless of input size
- [ ] this is `specs/TESTING.md` V-18's claim, made a gate rather than a benchmark line

### 0.10.2 — record-oriented streaming
- [ ] JSON Lines and CSV consumed through a **fixed window** the caller advances — a 10 GB file with the caller holding one record at a time
- [ ] documented as the answer for inputs larger than memory (`EVENT_MODEL.md` §7), with a worked example in `examples/`
- [ ] the boundary case: a record larger than the window, and what the caller must do about it

### 0.10.3 — O-P6 answered
- [ ] the measurement written up: what a genuinely incremental `feed(bytes)` would cost (every scanning function becomes a resumable state machine) against what it would buy over the record-oriented path
- [ ] a decision recorded **either way**, with the numbers
- [ ] if the answer is yes, it becomes a post-1.0 cycle rather than being retrofitted here — the contract does not change, so it can wait

## Gate

The event path's allocation proven constant across 1 MB, 100 MB and 1 GB inputs,
for all four formats.

## Watch for

- **The `Document` path is *supposed* to allocate proportionally.** It holds the
  tree. The measurement's value is the contrast, and a reader of the record
  should come away knowing which layer to reach for.
- **A 1 GB test is slow and belongs behind a flag**, not in the default run. The
  1 MB/100 MB pair runs always; the 1 GB leg runs in CI nightly and at every
  cycle close.
