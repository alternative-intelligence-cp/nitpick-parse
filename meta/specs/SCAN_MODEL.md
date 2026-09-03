# Scanning: the cursor, spans, text, and arithmetic that cannot trap

`src/scan/` is the layer every format shares and the reason this library exists:
what the prototype's five format parsers each rewrote was not the grammar, it
was this. It declares **no errors** and performs **no I/O**.

---

## 1. The cursor

```nitpick
pub struct:Cursor = {
    uint8[]:src;        // the caller's bytes — a borrow, never copied
    int64:pos;          // the read position, 0 <= pos <= src.len
};
```

**Rule C-1 (PA-010) — the caller owns the input, and `nparse` never reads a
file.** There is no `parse_file`. A caller who has a path reads it with the
prelude's `read_file` and hands the bytes over. This is what keeps the library
free of syscalls (`SAFETY.md` §2), free of a descriptor lifetime, and testable
from a byte literal.

**Rule C-2.** `Cursor` holds a **borrow** (`uint8[]`, D-070), so it is second
class: it cannot be returned from a function, stored in something that outlives
the call, or held across an `await`. Every parser therefore takes its cursor as
a field of a value the *caller* holds, and the borrow is re-derived from the
caller's input at each entry. `EVENT_MODEL.md` §5 states the consequence for
the public API.

**Rule C-3 — the operations, and all of them are total.**

| Operation | Answer |
|---|---|
| `cur_peek(c)` | the byte at `pos`, or `NIL` at the end |
| `cur_peek_at(c, k)` | the byte at `pos + k`, or `NIL` |
| `cur_bump(c)` | advances one byte; a no-op at the end |
| `cur_take(c, n)` | advances `min(n, remaining)`; returns how many |
| `cur_at_end(c)` | `pos >= src.len` |
| `cur_remaining(c)` | `src.len - pos`, never negative |
| `cur_slice(c, lo, hi)` | the borrowed `uint8[]` between two positions, clamped |

None of them fails, none of them traps, and none of them can be given an
out-of-range position that produces anything but a clamp. **A total cursor is
what lets a format's code read like the grammar** instead of like a bounds
check with a grammar inside it.

---

## 2. Spans

```nitpick
pub struct:Span = { uint32:lo; uint32:hi; };    // byte offsets, half-open
```

**Rule C-4 (PA-011) — a span is byte offsets, and line/column is computed on
demand.** Nothing tracks a line counter while scanning.

*Reasoning.* A line/column pair maintained per byte costs a branch on every
byte of every parse to serve a case that arises once per *error*, and errors
are rare. `scan_line_col(src, offset)` counts newlines from the start of the
input when a diagnostic is rendered. For a 1 GB input with one error that is one
extra pass over the bytes, once, on the path where a human is already reading a
message.

**Rule C-5 — `uint32` offsets, and the input bound follows from it.**
`NPARSE_MAX_INPUT` is 2^47 in `SAFETY.md` §7 for the cursor's *arithmetic*
proof, but a `Span` addresses 4 GiB. An input larger than `0xFFFFFFFF` bytes is
refused at entry with `EParseState` — a caller mistake, not an input's — because
a span that silently truncated would put a diagnostic on the wrong line, which
is worse than a refusal.

**Rule C-6 — `scan_line_col` is one-based for humans and the raw offsets are
zero-based for machines**, and the two never mix: the rendering function is the
only place a one-based number exists.

---

## 3. Byte classification

**Rule C-7.** The character classes every format needs live here once, as
`never fails` predicates over `uint8`: `is_space`, `is_newline`, `is_digit`,
`is_hex_digit`, `is_alpha`, `is_alnum`, `is_control`, `is_ascii`. Each is a
table lookup or a range compare, and each is total over all 256 values.

**Rule C-8 — a 256-byte class table, not a chain of comparisons.** One
`uint8[256]` of class bits, generated at cycle 0.1 and committed as source. The
formats differ in *which* classes they care about, never in what a class means.

---

## 4. UTF-8

**Rule C-9 (PA-013) — validation is explicit and per-format.** `nparse` does
not assume the input is UTF-8 and does not validate it globally. JSON requires
UTF-8 and validates; CSV does not and passes bytes through; TOML requires it
for strings and keys; YAML requires it. Each format states which, in
`FORMATS.md`.

*Reasoning.* A CSV file of Latin-1 exported from a spreadsheet is a real thing a
caller hands you, and a library that refused it would be wrong. A JSON document
that is not UTF-8 is malformed by RFC 8259 §8.1 and accepting it is a
vulnerability. The two answers differ, so the decision belongs to the format.

**Rule C-10.** The decoder accepts exactly the well-formed sequences of Unicode
Table 3-7: no overlongs, no surrogates (`U+D800`…`U+DFFF`), nothing above
`U+10FFFF`, and per-lead-byte continuation ranges rather than a general
"continuation byte" rule.

**Rule C-11 — `scan_utf8(c) -> Optional<Utf8Step>`** where `Utf8Step` is
`{ uint32:cp; uint8:len; }`. `NIL` means ill-formed at this position. The
*policy* on ill-formed input — reject, or substitute `U+FFFD` — is the format's,
not the scanner's.

**Rule C-12 — the codepoint accumulation is checked** like every other
accumulation (§5). A four-byte sequence accumulates into a `uint32` and cannot
overflow it, but the check is written anyway because the rule in §5 admits no
exceptions and an unchecked accumulation is the thing a reader has to reason
about.

---

## 5. Arithmetic that cannot trap

**This is the section that matters most.** `SAFETY.md` §4 states the rule; this
states the mechanism and enumerates every site.

**Rule C-13 (PA-012).** Three helpers in `src/scan/arith.npk` are the **only**
places in the library where an input-derived value is multiplied or added:

```nitpick
pub func:scan_mul_add = uint64?(uint64:acc, uint64:base, uint64:digit, uint64:bound)
    never fails;      // NIL when acc*base+digit would exceed bound
pub func:scan_add     = uint64?(uint64:a, uint64:b, uint64:bound) never fails;
pub func:scan_shift   = uint64?(uint64:acc, uint64:bits, uint64:bound) never fails;
```

Each checks **before** the operation:

```nitpick
// scan_mul_add, in full, because the order of the checks is the whole point.
if (base == 0u64) { pass NIL; }
if (digit > bound) { pass NIL; }
uint64:room = (bound - digit) / base;      // bound >= digit, base > 0: total
if (acc > room) { pass NIL; }              // acc*base would exceed bound-digit
pass (acc * base + digit);                 // proven in range
```

The subtraction is safe because `digit > bound` was refused; the division is
safe because `base == 0` was refused; and the multiply-add is safe because
`acc <= (bound - digit) / base`. **No branch of this function can trap for any
inputs.** It is the first `prove` site in `VERIFICATION.md` §4.

**Rule C-14 — the enumerated sites.** Every input-derived accumulation in the
library, and the bound each uses:

| Site | Accumulates | Bound | On overflow |
|---|---|---|---|
| decimal integer | digits base 10 | `INT64_MAX` or `UINT64_MAX` by sign | `Fault(NumberOutOfRange)` |
| hexadecimal integer (TOML) | digits base 16 | as above | as above |
| octal / binary integer (TOML) | base 8 / base 2 | as above | as above |
| decimal exponent | digits base 10 | `NPARSE_MAX_EXPONENT` | `Fault(NumberOutOfRange)` |
| `\uXXXX` escape | 4 hex digits | `0xFFFF` | `Fault(BadEscape)` |
| `\U00XXXXXX` escape (TOML) | 8 hex digits | `0x10FFFF` | `Fault(BadEscape)` |
| UTF-8 codepoint | continuation bytes | `0x10FFFF` | `NIL` from `scan_utf8` |
| span end | `lo + len` | `0xFFFFFFFF` | `EParseState` (C-5) |
| member count | `+1` per member | `NPARSE_MAX_MEMBERS` | `Fault(TooManyMembers)` |
| depth | `+1` per container | `NPARSE_MAX_DEPTH` | `Fault(DepthExceeded)` |
| scratch length | `+n` per append | `NPARSE_MAX_SCALAR` | `Fault(ScalarTooLong)` |

**Rule C-15 — a tree check enforces it.** `check_no_raw_accumulate`
(`TESTING.md` §3) greps `src/scan/` and `src/format/` for `*` or `+` applied to
a name matching an accumulator convention outside `arith.npk`, and fails the
run. It is a crude check and it is the right kind: the failure it prevents is
somebody writing the obvious three lines in a hurry.

**Rule C-16 — digit count is bounded before value.** A literal is refused at
`NPARSE_MAX_DIGITS` (4096) regardless of its value, so a megabyte of `0`s does
not spend a megabyte of checked multiplies proving it is still zero.

---

## 6. Numbers are scanned, not materialised

**Rule C-17 (PA-033).** The scanner **classifies** a numeric literal and
records its span; it does not decide what type it is.

```nitpick
pub enum:NumKind = { Integer; Float; };
pub struct:NumInfo = { NumKind:kind; Span:span; bool:neg; uint8:base; bool:big; };
```

`big` means "the value did not fit the 64-bit accumulator" — the literal is
still *well-formed*, and the caller may still want it as an `int256`, a `frac`,
or a decimal string. A parser that had already decided "this is an `int64` and
it overflowed" would have thrown that away.

**Rule C-18 — materialisation is the caller's, through named accessors**
(`VALUE_MODEL.md` §7): `num_int64`, `num_uint64`, `num_flt64`, `num_int256`,
`num_text`. Each returns an `Optional` and each is total.

*Reasoning.* JSON's grammar admits arbitrary-precision decimals and every
implementation quietly picks IEEE-754 double; TOML specifies `int64` and
`flt64` exactly; CSV has no types at all. A library that picked one
representation would be wrong for two of the three. Keeping the literal as text
plus a classification until somebody asks is the only answer that serves all
three, and Nitpick has `int256` and `frac64` for the callers who need them.

**Rule C-19 — float conversion is the one place `nparse` is allowed to be
inexact**, and it says so: `num_flt64` produces the nearest `flt64`, ties to
even, and a literal whose exact value is not representable converts with the
loss the IEEE format implies. `num_text` is always available for a caller who
cannot accept that.

---

## 7. Escapes and the scratch

**Rule C-20 (PA-014) — the common case copies nothing.** A scalar with no
escape sequence is a `TextRef` into the caller's input. Only a scalar that
*contains* an escape is rewritten, into the parser's scratch `Bytes`, and its
`TextRef` points there instead.

```nitpick
pub enum:TextSrc = { Input; Scratch; };
pub struct:TextRef = { TextSrc:src; uint32:lo; uint32:hi; };
```

**Rule C-21.** The scratch is cleared at the start of each scalar, so its
lifetime is one event. A caller that needs a scalar's text beyond the next
`parse_next` **copies it** — `EVENT_MODEL.md` §5 states this as the API's one
lifetime rule, and it is the rule most likely to be got wrong, so the
`Document` builder (which copies into the pool) is the answer for anyone who
does not want to think about it.

**Rule C-22 — escape decoding is per-format** but the *primitives* are shared:
`scan_hex4`, `scan_hex8`, `scan_surrogate_pair`. JSON's `😀` pair and
TOML's `\U0001F600` reach the same codepoint through the same checked
accumulation.

**Rule C-23 — an unpaired surrogate is a `Fault`**, not a substitution. JSON
permits an implementation to accept a lone surrogate and the result is a string
that cannot be encoded as UTF-8, which is how a validator and a consumer end up
disagreeing about the same document. The library refuses it and says so.

---

## 8. What the scanner deliberately is not

- **Not a lexer generator, and not a regex engine.** Every format here is
  scannable by a hand-written cursor. The prototype's `nparse` wired a Thompson
  NFA in as a modal lexer backend, which was right for the *general language
  front end* it was trying to be and is wrong for this library
  (`BUILD.md` §4, PA-007).
- **Not incremental.** Re-parsing a changed document re-parses it. Incremental
  reparse needs a lossless concrete syntax tree, a different value model, and a
  different library — `PLUGIN_MODEL.md` §7 says what that library would be.
- **Not error-recovering by itself.** Recovery is a policy the *format* applies
  (`DIAGNOSTIC_MODEL.md` §5); the scanner has no opinion about what to skip.

---

## 9. Open items

- **O-P2 — `NPARSE_MAX_SCALAR`.** See `SAFETY.md` §9; measured at cycle 0.3.
- **O-P3 — whether `scan_line_col` should memoise.** A document with a thousand
  errors would scan from the start a thousand times, which is quadratic. **Open
  by design:** it is a *measurement*, taken at cycle 0.9 when recovery makes
  many-error documents real, and the answer is either "leave it" or "build a
  line-start index once, on the first diagnostic".
