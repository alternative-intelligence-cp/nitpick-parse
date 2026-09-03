# Verification obligations

The compiler's cycle 1.5 makes `prove`, `requires`/`ensures`, `limit<Rules>`
and Z3 real. Its orchestration rules say that **every branch records its own
verification obligations and the orchestrator merges them** (R9), because
parallel authorship of library code is parallel authorship of proof
obligations, and obligations discovered in a branch and never collected are the
cheapest way to lose the campaign.

This document is `nparse`'s list. It is written **before** the code, kept
current as the code lands, and is the input `nparse` hands to the compiler's
obligation manifest when the verified build reaches libraries.

---

## 1. Where this stands

| Compiler subcycle | What it gives us | Our state |
|---|---|---|
| 1.5.0 (done) | the SMT writer, z3 under a pinned profile, the obligation manifest, `llvm.assume` elision | §3's bounds and §4's no-overflow obligations are already decidable |
| 1.5.1 | `limit<R>` names resolve, `Rules` bodies type, contract expressions type | §6's `limit` types become writable |
| 1.5.2 | `limit<Rules>` live | §6 lands |
| 1.5.3 | contracts live | §§3–4's `requires`/`ensures` land |
| 1.5.4 | `prove` / `assert_static` | §5's inline proofs land |
| 1.5.8 | `stack-depth` obligations | §7 — the one this library most wants |

**Rule P-1.** Until a construct is live, its obligation is stated **as a comment
beside the code in the exact syntax it will take**, and is enforced by a
property test. The switch is then deleting a comment marker rather than
inventing the clause. The compiler's rungs refuse the constructs by name today,
so a premature `ensures` is a build failure, not a silent no-op.

---

## 2. What the language discharges for free

- **Every index into a slice, array or `buffer` is bounds-checked** and traps
  (D-070). The question is only whether a *reachable* index is out of range,
  which is §3.
- **Every plain integer `+ - *` traps on overflow** (D-210) — which for this
  library is not a gift but the hazard itself (§4).
- **Division by zero traps** (D-007).
- **Borrows cannot escape** (D-004), so a `TextRef`'s resolution cannot outlive
  its input within a call.
- **Owning values are move-only** (TYPE-046), so no `Document` is aliased.
- **`Result<T>` everywhere** (D-163), so no error is dropped.

---

## 3. Bounds

**Rule P-2 — every index goes through one accessor pair per container**, and the
accessor is where the bound is checked (`SAFETY.md` S-12). That makes the bound
one obligation to discharge rather than several hundred.

```nitpick
func:cur_at = uint8(Cursor->:c, int64:k)
    requires (k >= 0i64 && k < c.src.len)
    never fails { … };
```

| Site | Obligation | How discharged |
|---|---|---|
| `cur_at`, `cur_slice` | index and range within `src` | contract, Z3 |
| `Vec<T>` `at`/`set` | index `< count` | contract, Z3 |
| `Bytes` `view`/`at` | offset + length `<= len` | contract, Z3 |
| pool read (`doc_text`) | `a + len <= pool.len` | contract, Z3 |
| depth stack push/pop | `count < NPARSE_MAX_DEPTH`; `count > 0` on pop | contract, Z3 |
| class table lookup | the index is a `uint8`, so `< 256` by type | free |
| `MapIndex` binary search | `lo <= hi` maintained; the loop terminates | invariant + variant, Z3 |

---

## 4. The no-overflow obligations — the library's core claim

**Rule P-3.** `SAFETY.md` §4 says no arithmetic may trap on any input. That is a
*verification* claim, and these are its obligations. They are the most valuable
rows in this document, because discharging them turns the library's central
safety property from "we tested it and fuzzed it" into "it is proven".

**`scan_mul_add`, in full** (`SCAN_MODEL.md` §5), is the flagship:

```nitpick
pub func:scan_mul_add = uint64?(uint64:acc, uint64:base, uint64:digit, uint64:bound)
    ensures (result == NIL || (raw result) <= bound)
    never fails { … };
```

with three internal `prove` sites establishing that no operation in the body can
trap:

| Operation in the body | Obligation |
|---|---|
| `bound - digit` | `digit <= bound` — established by the guard above it |
| `(bound - digit) / base` | `base != 0` — established by the first guard |
| `acc * base` | `acc <= (bound - digit) / base`, so the product `<= bound - digit` |
| `+ digit` | the sum `<= bound`, which is `ensures` |

**Rule P-4 — discharging these four is the highest-value verification work in
the library**, because every numeric literal in every format flows through this
one function. It is also the shape most likely to discharge: four scalar facts
over unbounded `Int` with explicit range axioms, which is exactly the
partitioned-integer encoding the compiler's D-218.4 describes.

**Rule P-5 — the other accumulation sites** (`SCAN_MODEL.md` C-14's table) are
discharged by *construction*: each calls `scan_mul_add` or `scan_add` with a
bound, so the obligation is the callee's precondition and the caller's proof is
that it passed a bound. `check_no_raw_accumulate` (`TESTING.md` §3) is what
makes "each calls the helper" true, and it is the reason a crude grep is worth
having beside a proof.

---

## 5. `prove` sites

**Rule P-6.** Inline `prove(…)` where a local fact is cheap to state and
expensive to lose:

| Site | Proof |
|---|---|
| after a UTF-8 decode | the length is 1…4 and the codepoint is a scalar value (not a surrogate, `<= 0x10FFFF`) |
| after any `scan_*` step | the cursor advanced, or the step reported `Done`/`Fault` — **the termination property** |
| after a span is built | `lo <= hi` and `hi <= src.len` |
| after a depth push | `depth <= NPARSE_MAX_DEPTH` |
| in the key/value alternation | a `Map` node's chain length is even (`VALUE_MODEL.md` D-5's off-by-two) |
| after `num_int64` | the magnitude is within `INT64_MAX`, or the answer is `NIL` |

**Rule P-7 — "the cursor advanced" is the one worth naming.** It is the
property a hand-written parser loses when somebody adds a production that can
match empty, and the symptom is a hang rather than a wrong answer. A `prove`
there turns an infinite loop into a compile error, and it is the obligation this
library would most like to have discharged.

---

## 6. `limit<Rules>`

**Rule P-8.** When 1.5.2 lands:

```nitpick
Rules:Offset  = { $ <= 4294967295u64; };        // a Span bound (SCAN_MODEL C-5)
Rules:Depth   = { $ <= 128u32; };
Rules:Base    = { $ == 2u64 || $ == 8u64 || $ == 10u64 || $ == 16u64; };
```

`Base` is the interesting one: it makes `scan_mul_add`'s `base != 0` guard
provable at the *caller* rather than checked at the callee, which is exactly the
D-218.9 elision payoff — the guard disappears from the inner loop of every
numeric scan.

---

## 7. Termination and depth

**Rule P-9.** Every loop is bounded by a value that decreases, and the bound is
stated:

| Loop | Variant |
|---|---|
| every `scan_*` | bytes remaining (P-7) |
| the parser's driver | bytes remaining, plus the depth stack's height |
| `doc_build` | events remaining |
| the document walk, compare, print, drop | nodes remaining × the explicit stack's height |
| `MapIndex` binary search | `hi - lo`, halving |
| the digit loop | `NPARSE_MAX_DIGITS` |

**Rule P-10 — the depth obligation is the compiler's 1.5.8 `stack-depth` kind**
and it is the one `nparse` most wants, because `SAFETY.md` §5's rule ("no
native recursion on an input-controlled path") is currently held by a **grep**
(`check_no_recursion`) rather than by a proof. When 1.5.8 lands, that check
becomes a discharged obligation and the exceptions table becomes provably
empty.

---

## 8. What cannot be proven, and is stated instead

**Rule P-11 — the honest claim.** Following the compiler's TCB doctrine
(`TCB.md`, D-218.11: *verified middle-end plus validated floor*), `nparse`'s
verification claim covers **its own arithmetic, its bounds and its
termination**, and does not and cannot cover:

- **conformance to a format's specification.** That a document `nparse` accepts
  is valid JSON is established by JSONTestSuite, which is *testing*, not proof.
  No corpus is exhaustive and none claims to be.
- **the corpora themselves**, whose contents are their authors'.
- **`flt64` conversion accuracy**, which is the prelude's Dragon4
  (`WRITER_MODEL.md` W-7) and is inherited rather than re-proved.
- **`llc` and `ld.lld`**, which the compiler names as trusted components.

**Rule P-12 — the residue is enumerated rather than mitigated**, which is the
seL4 precedent the compiler cites and the only honest shape for a claim of this
kind.

---

## 9. The handoff

**Rule P-13.** When the compiler's verified build reaches libraries, `nparse`
hands over: this document's obligation list, the `nitpick.obligations` rows its
own build produces, and the property tests that stood in for each unproven row.
Cycle 0.13 owns that handoff, and R9 is why it is a deliverable rather than a
hope.
