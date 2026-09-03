# Diagnostics

`ParseError` — the value a `Fault` carries. This is where the richness that
would otherwise have been thirty `error:` identities lives.

---

## 1. Why it is a value

`SAFETY.md` §3 has the argument and it is worth one sentence here: an `error:`
identity costs every consuming program a mandatory `failsafe` arm, and a library
that reads hostile input must not be able to stop a program with a bad byte. So
the detail rides in the **success** channel, in a value, and `pick`
exhaustiveness makes the caller look at it.

---

## 2. The value

```nitpick
pub struct:ParseError = {
    FaultCode:code;      // 2 bytes — the closed enum, §3
    uint16:flags;        // 2 — FL_RECOVERABLE, FL_AT_END, FL_IN_KEY
    Span:span;           // 8 — where, in the input
    uint32:expected;     // 4 — a bitmask of TokenClass, §4
    uint32:found;        // 4 — the byte or token class actually present
    uint32:depth;        // 4 — the nesting depth at the fault
};                       // 24 bytes, align 4
```

**Rule F-1 — no owning field**, so it rides inside `Step.Fault(ParseError)`,
sits in a `Vec` when recovery collects several, and copies freely.
`#size_of<ParseError>()` is asserted at 24.

**Rule F-2 — the span is always valid and always within the input**, and
`lo <= hi`. A fault at end of input has `lo == hi == src.len` and `FL_AT_END`.
This is one of the plugin conformance obligations (`PLUGIN_MODEL.md` §5) because
a diagnostic pointing outside the document is worse than none.

**Rule F-3 — no message text is stored.** Rendering is a function of the value
(§6), so messages stay free to improve, translations become possible, and the
struct stays 24 bytes with no owning field. This is the same reason the
compiler's own tests assert on codes and never on text.

---

## 3. The code enum

**Rule F-4 (PA-040) — one closed enum for the whole library**, format-neutral
where it can be and format-specific where it must be.

| Code | Means |
|---|---|
| `UnexpectedByte` | a byte that no production admits here |
| `UnexpectedEnd` | input ended inside a construct |
| `ExpectedValue` | a value was required |
| `ExpectedKey` | a map key was required |
| `ExpectedSeparator` | a `,`, `:`, `=` or newline was required |
| `ExpectedCloser` | a `}`, `]` or terminator was required |
| `TrailingContent` | the document ended and bytes remain |
| `BadEscape` | an escape sequence is malformed or out of range |
| `BadUtf8` | ill-formed UTF-8 where the format requires it |
| `UnpairedSurrogate` | a lone surrogate half (`SCAN_MODEL.md` C-23) |
| `NumberOutOfRange` | a numeric literal exceeds what the format allows |
| `NumberMalformed` | a numeric literal is not well-formed |
| `DuplicateKey` | a key repeated in one map (`VALUE_MODEL.md` §6) |
| `DepthExceeded` | nesting beyond `NPARSE_MAX_DEPTH` |
| `ScalarTooLong` | a scalar beyond `NPARSE_MAX_SCALAR` |
| `KeyTooLong` | a key beyond `NPARSE_MAX_KEY` |
| `TooManyMembers` | a container beyond `NPARSE_MAX_MEMBERS` |
| `BadIndent` | indentation is inconsistent (YAML) |
| `BadTable` | a table header is malformed or redefines (TOML) |
| `BadRow` | a row's field count disagrees with the header (CSV) |
| `Unsupported` | a construct this format's supported subset excludes |
| `FormatSpecific` | a third-party format's own code, in `found` |

**Rule F-5 — `Unsupported` is not `UnexpectedByte`.** A YAML anchor is
*well-formed YAML* that this library's subset excludes (`FORMATS.md` §4), and
telling a user "unexpected `&`" when the truth is "anchors are not supported"
wastes their afternoon. Every construct the subsets exclude reports
`Unsupported` and the renderer names the construct.

**Rule F-6 — the enum is closed and adding a variant is a major version**
(PA-009), because a consumer's exhaustive `pick` over `FaultCode` breaks.
`FormatSpecific` exists so a third-party format never needs one (O-P7).

---

## 4. `expected` and `found`

**Rule F-7.** `expected` is a bitmask over `TokenClass` — `TC_VALUE`,
`TC_STRING`, `TC_NUMBER`, `TC_LBRACE`, `TC_RBRACE`, `TC_LBRACKET`,
`TC_RBRACKET`, `TC_COMMA`, `TC_COLON`, `TC_EQUALS`, `TC_NEWLINE`, `TC_EOF`, and
a dozen more. A mask rather than a list because it is 4 bytes with no
allocation and no owning field, and because "one of these" is what a parser
actually knows.

**Rule F-8 — `found` is the byte when the code is `UnexpectedByte`**, and a
`TokenClass` otherwise, discriminated by the code. Two meanings in one field is
exactly the shape D-069 removed from `Result`, so it is stated here explicitly
and the accessor pair `fault_found_byte` / `fault_found_class` is the only way
to read it — a caller never touches the field.

*This is a compromise and it is recorded as one.* The alternative is two fields
and a 28-byte struct; the accessors make the discrimination unforgeable, which
is what the D-069 objection was actually about.

---

## 5. Recovery

**Rule F-9 (PA-042) — recovery is opt-in and bounded.** With
`Options.max_errors == 0` (the default) the first fault ends the parse. With a
positive value the parser attempts to resynchronise and continues, collecting up
to that many faults.

**Rule F-10 — resynchronisation is per format and is stated per format**
(`FORMATS.md`), because there is no format-neutral answer: JSON resynchronises
at the next `,` or closer at the current depth; TOML at the next line beginning
a key or a table header; CSV at the next record separator; YAML at the next line
at or below the current indentation.

**Rule F-11 — recovery never invents structure.** A recovered parse produces the
events it could read and the faults it could not; it does not fabricate a
closing brace to balance the stream. A consumer that builds a `Document` from a
recovered parse gets `Fault` from `doc_build` regardless (`VALUE_MODEL.md`
D-22) — recovery serves a *diagnostic* consumer, such as a linter reporting
every problem in a file, not a data consumer.

**Rule F-12 — recovery is not on the round-trip path.** A recovered parse is
not re-printable and the oracle does not run on one. Stated because "print what
we recovered" is the obvious next idea and it would produce a document that
differs from the input in ways nobody chose.

---

## 6. Rendering

**Rule F-13 (PA-041) — rendering is a function, not a format string.** Nitpick
has no format-specifier language (D-053): `printf` and its relatives do not
exist, and there is nothing for a message template to be interpreted by.

```nitpick
pub func:fault_render = NIL(ParseError:f, uint8[]:src, string:name, Bytes->:sink);
```

writes a diagnostic in the compiler's own shape:

```
NPARSE-0007 config.toml:14:9: expected `=` after key, found newline
   14 | title "example"
      |       ^
```

**Rule F-14 — the code is stable and the message is not.** `NPARSE-nnnn` is
derived from the `FaultCode` and never changes meaning; the prose after it is
free to improve. Every test asserts on the code (`TESTING.md` §2), never on the
text — the compiler's own rule, for the same reason.

**Rule F-15 — line and column are computed here and nowhere else**
(`SCAN_MODEL.md` C-4). The renderer is the only caller of `scan_line_col`, and
it is the only place a one-based number exists.

**Rule F-16 — the caret line is built from display columns, not bytes.** A
fault after a CJK character or an emoji points at the right place only if the
underscore count is a *width*, not a byte count. `nparse` does not carry Unicode
width tables and will not (it is `ntui`'s domain, and duplicating them here
would be two tables to keep in sync) — so **the caret line counts codepoints,
and the documentation says so**. A consumer that has width tables renders its
own caret from the span, which is why the span is the thing the library
guarantees and the caret is a convenience.

---

## 7. Open items

- **O-P7 — the third-party code mechanism.** `FormatSpecific(uint16)` versus a
  reserved band in the closed enum. **Recommendation:** `FormatSpecific`, because
  a reserved band is a band somebody eventually collides in. Decided at cycle
  0.9. Mirrored in `PLUGIN_MODEL.md` §8.
- **O-P10 — whether `fault_render` should be able to render *several* faults
  with shared context** (a linter printing twenty problems re-scans for line
  starts twenty times, O-P3's quadratic). **Open by design:** measured at cycle
  0.9 alongside O-P3, and the two share an answer.
