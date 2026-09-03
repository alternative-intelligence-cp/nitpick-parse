# Safety, errors, and the limits

The constraints. Read this first: most designs that look reasonable for a
parsing library die on one of §1's rules, and the two that shape `nparse` most
— **a syntax error is a value** and **arithmetic on input must not trap** —
have no analogue in any other language's parsing library, so there is nothing
to copy.

---

## 1. What the language imposes

Each row is a language decision, not ours. The consequence column is what it
costs a library that reads bytes somebody else controls.

| Language rule | Where | Consequence for `nparse` |
|---|---|---|
| `failsafe`'s `pick` must **name** every error that can reach it | REACH-002 | Every public `error:` we declare is an arm every consuming program owes. §3. |
| Reachability is **import-scoped** | 1.4.8's `nsys` note | Module decomposition decides what a consumer's `failsafe` owes. §3. |
| Plain integer `+ - *` **traps** on overflow | D-210 | `acc = acc * 10 + d` is a **remote crash**. §4 — this is the biggest one. |
| `/` and `%` by zero trap | D-007, D-142 | A divisor from input is checked before use. §4. |
| Indexing is bounds-checked and traps | D-070 | An index derived from input is a *crash*, not a smear. §4. |
| There is **no stack-depth guard**, and `stack-depth` is a 1.5.8 obligation kind | VERIFICATION_REFERENCE §365 | Native recursion on input-controlled depth is a stack overflow. §5. |
| **A mutable module-level binding is refused** | D-211 | All parser state is a value the caller holds. §6. |
| Owning values are **move-only** | TYPE-046 | No value stored in an array or an arena may own anything. §6. |
| An arena `get` returns a **copy** | D-152, MEMORY_REFERENCE §4.2 | A `Document` node holding a `string` could not be read back **at all**. §6. |
| `string_slice` allocates an **owned copy** | D-186 | A parser that sliced per token would allocate per token. §6. |
| Borrows are second class | D-004 | A `uint8[]` view of the input cannot be returned, stored past the call, or held across `await`. §6. |
| There are **no closures** | D-018 | A push parser's visitor would be a trait object plus hand-carried context. EVENT_MODEL.md §2. |
| There are **no static methods** | D-185 | Construction is a bare function: `json_reader(input)`, never `JsonReader.new(…)`. |
| There is **no map or hash container** | measured; nothing in TYPE_REFERENCE or the prelude | We scan a small ordered array, or build an index deliberately. VALUE_MODEL.md §5. |
| `Default` is not derivable | D-123 | A dialect's defaults are a named constructor, not a derive. |
| Operator overloading is forbidden | OP_REFERENCE | `a.eq(b)` on anything that is not a scalar; `string_equals` for strings. |
| `defer` does **not** run on a trap | D-014 | There is no cleanup we can rely on after a trap — so we must not trap. §4. |
| A successful `exit 0` with live `wild` allocations **traps** | D-151 | Every `wild` byte is paired on every path. §6. |

---

## 2. What `nparse` does *not* need, and the freedom that buys

Worth stating up front because it removes half the hazards the other libraries
in this ecosystem carry:

- **`nparse` makes no syscall.** It reads no file, opens no descriptor, spawns
  no process, installs no signal handler, and touches no device. The caller
  hands it bytes. Consequently there is no trap path to protect, no restore
  record, no `signalfd`, and **nothing in this library is Linux-specific or
  x86-64-specific** (PA-006).
- **`nparse` has no concurrency.** No task, no channel, no lock, no `await`.
  Every function is synchronous, which means `raw` is licensed wherever a
  callee is genuinely `never fails` (D-163) and the whole `async` rule set is
  simply absent.
- **`nparse` has no clock and no environment.** Same input, same output, on
  every machine, forever. That is what makes the round-trip oracle
  (`TESTING.md` §4) a fact rather than an approximation.

The hazards it *does* carry are entirely in §§3–5, and they are all one
hazard wearing three hats: **the input is hostile.**

---

## 3. The error budget — two, and no input can produce either

**Rule S-1 (PA-008).** REACH-002 makes every `error:` that can reach `failsafe`
a named arm the consuming program's `failsafe` must carry, and an unhandled one
stops the process. For a library whose entire job is reading bytes somebody
else controls, **routing malformed input through that channel would mean a bad
byte can stop a program.** So it does not.

`nparse` declares exactly two public error identities:

| Error | Raised when | Can an input cause it? |
|---|---|---|
| `EParseState` | the API was used out of order, or an option is incoherent — a `Dialect` whose delimiter equals its quote, a depth bound of zero, a writer handed a `Document` from a destroyed arena | **No** |
| `EParseEncode` | a `Document` cannot be represented in the target format — a NaN in JSON, a top-level scalar in TOML, a map key that is not a string | **No** |

Both are **caller mistakes**. Neither is reachable from any byte stream.

**Rule S-2 — every condition an input can cause is a `Fault` value.**
`parse_next` answers `Step`:

```nitpick
pub enum:Step = { Ev(Event); Fault(ParseError); Done; };
```

`ParseError` is a plain 24-byte value (`DIAGNOSTIC_MODEL.md` §2) carrying a
closed code enum, a span, an expected set and what was found. It travels in the
**success** channel.

**Rule S-3 — `pick` exhaustiveness is what forces the caller to handle it.**
This is the whole argument for the design, and it is stronger than a `Result`
would be. A caller who receives a `Result` can write `?| default` and silently
swallow a malformed document, or `?!` and turn it into a trap. A caller who
receives a `Step` **must write a `Fault` arm**, because the compiler refuses a
non-exhaustive `pick` (`CONTROL_REFERENCE.md` §1.2). The language's own
exhaustiveness rule does the work an `error:` identity would only pretend to do.

**Rule S-4 — three is a major version.** A third identity is added only by a
recorded decision that says why a *shutdown handler* would treat the failure
differently from the two, and it is a **major** version change under PA-009
because it is a new mandatory arm in every consumer — a compiler-enforced
source break. If the trigger is something a byte stream can cause, a third
identity is the wrong answer and the design is what needs changing.

**Rule S-5 — forwarded codes cost no arm.** Where a prelude error reaches a
caller — a stale arena handle is `StaleHandle` (−4106), a writer's sink returns
an errno — it is forwarded verbatim (`fail r.err`). A dynamic operand does not
enlarge the reachable set, so it costs no `failsafe` arm.

**Rule S-6 — module decomposition is part of the budget**, because REACH is
import-scoped:

- `nparse/scan.npk`, `nparse/event.npk` and `nparse/diag.npk` declare **no
  errors at all**. A program that imports the scanner to tokenize its own
  format owes nothing.
- `nparse/doc.npk` and every `nparse/format/*.npk` declare **`EParseState`**
  only.
- `nparse/emit/*.npk` additionally declares **`EParseEncode`**.

**Rule S-7.** The exact arm set a consuming program owes, per import, is
generated into the documentation and checked by a conformance test that builds
a program importing each public module and asserts its `failsafe` compiles with
exactly the documented arms and no more. An out-of-date arm list is the kind of
document that goes stale silently, so it is derived, not written.

---

## 4. Arithmetic — the no-trap rule

**Rule S-8 (PA-012). No arithmetic anywhere in this library may trap on any
input.** Not on a malformed one, not on a hostile one, not on a merely long
one.

**The failure this exists to prevent.** The ordinary decimal accumulator is

```nitpick
acc = acc * 10i64 + (b - 48u8) => int64;      // WRONG — traps under D-210
```

and on `99999999999999999999999` — twenty-three digits, which anyone can type
into a JSON field — the multiply overflows and D-210 routes it to `failsafe`
with `IntOverflow`. **That is a remote denial of service in three lines of the
most obvious code in the library.** No other language's parser has this
failure, because no other language traps here; a C parser wraps and a Rust
parser wraps in release. In Nitpick it stops the program.

**The rule, concretely.** Every accumulation is range-checked *before* the
operation that could overflow:

```nitpick
// The digit is admissible only if the accumulator cannot exceed the bound.
if (acc > (BOUND - d) / 10i64) { pass (scan_overflow(sp)); }   // a Fault
acc = acc * 10i64 + d;
```

and the answer on overflow is a `Fault` with code `NumberOutOfRange`, never a
trap and never a wrap.

**Rule S-9.** The same discipline applies to every other arithmetic on an
input-derived quantity: a span's end, a repeat count, a length prefix, a
computed index, a UTF-8 codepoint accumulation, an exponent. **`SCAN_MODEL.md`
§5 enumerates every site**, and a tree check (`TESTING.md` §3)
greps `src/scan/` and `src/format/` for a bare `*` or `+` on an accumulator
outside the checked helpers.

**Rule S-10 — the helpers are the only spelling.** `scan_mul_add_checked`,
`scan_add_checked` and `scan_shift_checked` in `src/scan/arith.npk` are the
only places the library multiplies or adds an input-derived value, and each
returns an `Optional` that is `NIL` on overflow. Nothing else does the
arithmetic inline.

**Rule S-11 — division by an input-derived value is checked** for zero on the
same path, and the zero case is an answer (an empty result, a `Fault`), not a
trap.

**Rule S-12 — indexing.** Every index into the input, the scratch or a pool
goes through one accessor pair per container, and the accessor is where the
bound is checked. Callers do not index raw storage. This is what makes the
bound one obligation to discharge in cycle 1.5 rather than several hundred.

---

## 5. Depth — the explicit stack

**Rule S-13 (PA-022). There is no native recursion anywhere on a path whose
depth an input controls.** Not in the parsers, not in the tree builder, not in
the writers, not in the equality comparison, not in the drop.

**The failure this exists to prevent.** `[[[[[[[[…` repeated fifty thousand
times is eight bytes of shell and a stack overflow in a recursive-descent
parser. The language has no stack-depth guard — `stack-depth` is an obligation
kind scheduled for the compiler's 1.5.8 (`VERIFICATION_REFERENCE.md` §365) and
does not exist today — so the overflow is a raw fault, not a controlled stop.
That is the one failure mode this ecosystem exists to make impossible, arriving
through the front door.

**The rule.** Nesting is a `Vec<Frame>` the parser owns, `NPARSE_MAX_DEPTH`
deep. Exceeding it is a `Fault` with code `DepthExceeded`. The **writers** and
the **tree walk** carry their own explicit stacks for the same reason: a
`Document` fifty thousand levels deep can be *built* by a bounded parser and
then blow the stack when somebody prints it.

**Rule S-14.** `NPARSE_MAX_DEPTH` defaults to **128** and is a per-parse option.
128 is above anything a human writes and below anything that costs memory;
a program with a genuine reason raises it and owns the consequence.

---

## 6. Resources and representation

**Rule S-15 — nothing stored in an array or an arena owns anything.** `Event`,
`Node`, `ParseError`, `Frame` and every value in a `Vec` or an arena declare no
owning field. Two separate language rules force this and the second is the
sharper one:

- an owning field makes the type move-only (TYPE-046), so a `Vec` of them
  cannot be copied, cleared or compared; and
- **an arena `get` returns a copy** (D-152), and a copy of an owning value is
  *refused* — so a `Document` node holding a `string` could not be read back at
  all.

Text therefore lives in a side pool and is addressed by offset and length
(`VALUE_MODEL.md` §3).

**Rule S-16 — the caller owns the input and it is never copied.** The input is
a `uint8[]` borrow (PA-010). Scalar text is a `TextRef` into it. The only bytes
`nparse` copies are the ones an escape sequence forced it to rewrite, and those
go into a scratch `Bytes` the parser owns.

**Rule S-17 — all state is a value the caller holds.** There is no module-level
mutable state anywhere, which is not a preference: D-211 refuses it. The
prototype's five format parsers each kept their entire state — node table,
position, token, last error — in exactly such bindings, which is why none of
them is portable to the current language.

**Rule S-18 — every `wild` byte is paired on every path.** `Vec<T>`'s block is
`wild`; a scope that made one frees it, so `exit 0` never trips D-151. The test
programs exit 0 on purpose, so a leak on any path turns a pass into a trap.

**Rule S-19 — allocation is bounded by a stated function of the input.** The
parser's scratch is bounded by `NPARSE_MAX_SCALAR`; the depth stack by
`NPARSE_MAX_DEPTH`; a `Document` by the node and pool growth its arena does.
Nothing grows without a bound somebody can name.

---

## 7. The limits, in one table

Every bound is a named constant in `src/core/limits.npk` (PA-004), every one is
exercised by a case sitting exactly on it and one exceeding it, and none of them
is a loop over attacker-controlled length without one.

| Constant | Default | Bounds | Exceeding it |
|---|---|---|---|
| `NPARSE_MAX_DEPTH` | 128 | container nesting, in the parser, the builder, the writer and the walk | `Fault(DepthExceeded)` |
| `NPARSE_MAX_SCALAR` | 16 MiB | one scalar's decoded length (a single JSON string) | `Fault(ScalarTooLong)` |
| `NPARSE_MAX_KEY` | 64 KiB | one map key's decoded length | `Fault(KeyTooLong)` |
| `NPARSE_MAX_MEMBERS` | 2^31−1 | members in one container | `Fault(TooManyMembers)` |
| `NPARSE_MAX_DIGITS` | 4096 | digits in one numeric literal before scanning stops | `Fault(NumberOutOfRange)` |
| `NPARSE_MAX_EXPONENT` | 9999 | the magnitude of a decimal exponent | `Fault(NumberOutOfRange)` |
| `NPARSE_MAX_ERRORS` | 64 | faults collected in recovery mode before parsing stops | parsing stops; the collected set is returned |
| `NPARSE_MAX_INPUT` | 2^47 | the input length the cursor's arithmetic is proven over | `EParseState` (a caller mistake, not an input) |

**Rule S-20.** Every one of these is a per-parse option except `NPARSE_MAX_INPUT`,
which is a property of the cursor's arithmetic proof and is not adjustable.

---

## 8. What a consuming program owes

Stated once, here, and repeated in the public documentation:

1. **Handle the `Fault` arm.** The compiler will not let you do otherwise, but
   handling it by discarding is still a decision — a malformed document that
   silently becomes an empty one is the vulnerability this library's shape was
   chosen to prevent.
2. **Carry the `failsafe` arms your imports require** — at most `EParseState`
   and `EParseEncode`, and §7's generated list says exactly which per module.
3. **Keep the input alive while the events are alive.** A `TextRef` points into
   the caller's bytes. The borrow rules enforce it within a call; across calls
   it is the caller's discipline and it is stated in `EVENT_MODEL.md` §5.
4. **Destroy the `Document`'s arena.** An un-destroyed arena is a wild-role
   leak the exit-time check names (D-151).

---

## 9. Open items

- **O-P1 — the duplicate-key default.** Whether a repeated key in a map is an
  error, keeps the first, or keeps the last. **Recommendation: an error by
  default**, with a policy option, because parser differentials over duplicate
  keys are a documented vulnerability class and the formats disagree
  (TOML and YAML forbid; JSON leaves it undefined). Decided at cycle 0.4.
  Mirrored in `VALUE_MODEL.md` §6.
- **O-P2 — the scratch bound `NPARSE_MAX_SCALAR`.** 16 MiB is a guess, not a
  measurement. **Open by design:** it is confirmed at cycle 0.3 against the
  JSONTestSuite corpus and a realistic large-document sample, and the number
  chosen is recorded with the measurement.
