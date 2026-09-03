# The formats

Which formats ship at 1.0, which version of each, which subset, and what gates
it. **A format's claim in this document means there is a vendored conformance
corpus behind it and every case is judged** (PA-053) — a claim with a file
behind it rather than a claim.

---

## 1. The set at 1.0

| Format | Specification | Subset | Corpus | Cycle |
|---|---|---|---|---|
| **JSON** | RFC 8259 | **complete** | JSONTestSuite | 0.3 |
| **TOML** | v1.0.0 | **complete** | toml-test | 0.6 |
| **CSV** | RFC 4180 + dialects | **complete**, plus the dialects §6 names | hand-built + the W3C CSVW cases | 0.7 |
| **YAML** | 1.2 core schema | **a stated subset**, §4 | yaml-test-suite, filtered to the subset | 0.8 |

**Rule R-1 (PA-054) — the specification version is pinned and recorded**, in
`meta/research/format-versions.md`, with the document's own version string and
the date it was read. "TOML" without a version is three incompatible languages.

**Rule R-2 (PA-050) — four formats at 1.0, and the set is closed for that
release.** Each is a cycle, each has a corpus gate, and adding a fifth before
1.0 would mean four formats tested and one asserted.

---

## 2. JSON — RFC 8259, complete

**Rule R-3.** The whole grammar: objects, arrays, strings with all escapes,
numbers, `true`, `false`, `null`. UTF-8 required (RFC 8259 §8.1) and validated
(`SCAN_MODEL.md` C-9).

**Rule R-4 — the things RFC 8259 leaves to the implementation, decided:**

| Question | `nparse`'s answer | Why |
|---|---|---|
| duplicate object keys | `Fault(DuplicateKey)` by default | `VALUE_MODEL.md` §6 |
| number range | any well-formed literal parses; `ND_BIG` when it exceeds 64 bits | `VALUE_MODEL.md` D-19 |
| lone surrogates in `\u` escapes | `Fault(UnpairedSurrogate)` | `SCAN_MODEL.md` C-23 |
| a leading BOM | stripped when `allow_bom` (the default) | RFC 8259 forbids it, reality supplies it |
| nesting depth | `NPARSE_MAX_DEPTH`, default 128 | `SAFETY.md` §5 |
| trailing bytes after the value | `Fault(TrailingContent)` | |

**Rule R-5 — the extensions are not enabled and are not implemented.** No
comments, no trailing commas, no unquoted keys, no single quotes, no `NaN` or
`Infinity`. A caller who wants JSON5 wants a different format, and a permissive
JSON reader is how a validator and a consumer end up disagreeing.

**Rule R-6 — JSON Lines is an option on the JSON reader**, not a format:
`json_lines_reader` emits `DocStart`/`DocEnd` per line. It is the answer to
streaming a large file (`EVENT_MODEL.md` §7) and costs one flag.

**Rule R-7 — the gate is JSONTestSuite**, vendored, with every `y_` case
accepted, every `n_` case faulted, and every `i_` case producing a **recorded**
verdict that a change must not silently move. The `i_` set is the implementation-
defined one and recording our answer for each is how a future change to a
number or an escape rule becomes visible.

---

## 3. TOML — v1.0.0, complete

**Rule R-8.** The whole language: bare and quoted keys, dotted keys, basic and
literal strings, multi-line forms, integers in four bases, floats including
`inf` and `nan`, booleans, the four date-time types, arrays, inline tables,
tables, and arrays of tables.

**Rule R-9 — the four date-time types are scanned and classified, never
interpreted.** `ScalarKind` has `Date`, `Time` and `DateTime`, and the node
keeps the literal's text. `nparse` does **not** convert to a timestamp, does not
validate that 31 February is not a day, and does not know what a timezone is.

*Reasoning.* That is `ntime`'s job (O-P4), the two libraries cannot depend on
each other today (`BUILD.md` §4), and a parser that half-validated a date would
be a second, worse date library nobody asked for. What `nparse` guarantees is
that the *syntax* matches TOML's grammar (RFC 3339 shaped) and the span is
right; what the value means is the caller's, through `ntime` when it exists.

**Rule R-10 — TOML forbids duplicate keys and redefinition, and this is not
a policy option.** `DupPolicy` does not relax it (`VALUE_MODEL.md` D-15).
Redefining a table, or defining a key inside a table already closed by a later
header, is `Fault(BadTable)`.

**Rule R-11 — the table-header semantics are the hard part**, and they are why
TOML is a whole cycle: `[a.b.c]` implicitly creates `a` and `a.b`, `[[x]]`
appends, a dotted key inside an inline table cannot escape it, and a table
defined after a dotted key that already created it is an error. Every one of
these is a `toml-test` case and the corpus is the gate.

**Rule R-12 — the gate is toml-test**, vendored, both its `valid/` and
`invalid/` sets, with the valid set additionally checked against its expected
JSON encoding — which is a **second oracle** for free, independent of our own
round trip.

---

## 4. YAML — 1.2 core schema, a stated subset

**Rule R-13 (PA-051) — the subset, exactly.**

**In:**
- block mappings and block sequences, with indentation
- flow mappings `{}` and flow sequences `[]`
- plain scalars, single-quoted, double-quoted with escapes
- literal `|` and folded `>` block scalars, with the chomping and indentation
  indicators
- comments
- the core schema's resolution: `null`, `true`/`false`, integers, floats,
  strings
- explicit document markers `---` and `...`, with **exactly one document**

**Out, and each reports `Fault(Unsupported)` naming the construct:**
- **anchors `&` and aliases `*`** — and this is a security decision as much as
  a scope one: alias expansion is the "billion laughs" amplification vector,
  and a bounded implementation needs an expansion budget, a cycle detector and
  a size accounting that the rest of the library does not have
- **merge keys `<<`** — a semantic minefield that YAML 1.2 itself does not
  define, only a widely implemented convention
- **tags** beyond the core schema — `!!binary`, `!!timestamp`, `!Custom`; a tag
  system is a type system and it is not this library's
- **directives** `%YAML`, `%TAG`
- **multiple documents** in one stream
- **complex mapping keys** `? key` — a key that is itself a collection

**Rule R-14 — the subset is a decision, not a stage of completion.** Full YAML
is cycle 1.1 post-1.0, with anchors carrying an expansion budget as a first-class
part of the design rather than an afterthought. Shipping a "YAML parser" that
silently ignored anchors would be worse than one that refuses them by name.

**Rule R-15 — plain scalar resolution follows the core schema exactly**, and
the traps are stated: `no`/`on`/`off`/`yes` are **strings**, not booleans
(that is YAML 1.1's behaviour and the source of the Norway problem);
`0o7` is an integer and `07` is an integer in base 10 with a leading zero,
not octal; a value that looks like a sexagesimal is a string.

**Rule R-16 — the gate is the yaml-test-suite**, vendored, filtered to the
subset: every case tagged with an excluded construct must produce
`Fault(Unsupported)`, and every other case must match its expected event
stream. **The suite's own event format is close enough to ours that the
comparison is mechanical**, which is the largest single reason to adopt this
event vocabulary rather than invent one.

---

## 5. XML — out at 1.0

**Rule R-17 (PA-052).** Not shipped, and recorded as a decision rather than an
omission.

*Reasoning.* XML's data model is genuinely different: attributes are not
children, mixed content interleaves text and elements, and namespaces rewrite
names. The event vocabulary would need `Attribute` and a text-run notion, which
is a **major version** of the plugin interface (`PLUGIN_MODEL.md` §6) — so
adding XML later is a breaking change however it is done, and doing it *badly*
now to avoid one is the worst of both. On top of that, entities and DTDs are the
same amplification hazard as YAML anchors with thirty years more surface.

XML is post-1.0, with its own decision batch, and the event-vocabulary
extension is the first thing that batch decides.

---

## 6. CSV — RFC 4180 plus dialects

**Rule R-18.** RFC 4180 as the default dialect, with the departures that occur
in practice available as options:

```nitpick
pub struct:Dialect = {
    uint8:delim;         // ','
    uint8:quote;         // '"'
    bool:double_quote;   // true — "" is an escaped quote
    uint8:escape;        // 0 = none; some dialects use '\'
    bool:has_header;     // false
    bool:trim_fields;    // false
    bool:allow_ragged;   // false — a short or long row is Fault(BadRow)
    LineEnd:line_end;    // Any (default) | Lf | CrLf
};
pub func:dialect_rfc4180 = Dialect() never fails;
```

**Rule R-19 — CSV does not validate UTF-8** (`SCAN_MODEL.md` C-9). A
spreadsheet export in Latin-1 is a real file a caller hands over, and refusing
it would be wrong. Fields are `Raw` scalars: bytes, with no encoding claim.

**Rule R-20 — a CSV document is a sequence of sequences**, and with
`has_header` a sequence of **maps** keyed by the header row. Not a table type:
the event vocabulary already expresses both and a third shape would be a shape
only CSV used.

**Rule R-21 — `allow_ragged` defaults to false.** A row whose field count
differs from the header's is `Fault(BadRow)`, because a silently short row is
how a column shifts and nobody notices until the numbers are wrong.

**Rule R-22 — the gate** is a hand-built corpus plus the W3C CSVW test cases,
and it is the weakest gate of the four because CSV has the weakest
specification. That is stated rather than hidden, and the hand-built corpus is
correspondingly larger: every dialect combination, every quoting edge, embedded
newlines, embedded delimiters, a BOM, CRLF and LF and mixed, an empty file, a
header-only file, and a 100 MB file.

---

## 7. What every format owes

Beyond `PLUGIN_MODEL.md` §3's eight obligations, each shipped format states, in
its own module header and in this document:

1. **its specification version**, pinned (R-1);
2. **its subset**, if any, construct by construct;
3. **its UTF-8 policy** (C-9);
4. **its duplicate-key behaviour**, and whether `DupPolicy` affects it;
5. **its resynchronisation rule** for recovery (`DIAGNOSTIC_MODEL.md` F-10);
6. **its canonical output form** (`WRITER_MODEL.md` §3);
7. **its corpus**, and the exact expected-pass count.

---

## 8. Open items

- **O-P4 — the datetime overlap with `ntime`.** TOML has four date-time types;
  `nparse` scans and classifies them and interprets nothing (R-9). When
  dependency resolution lands (O-N1) and `ntime` exists, the question is whether
  `nparse` should gain an optional accessor that returns an `ntime` value.
  **Recommendation:** no — `nparse` keeps the text and the *caller* converts,
  because a parsing library that grew a date library inside it is how the
  duplication this library exists to end starts again. Revisit only if a
  consumer demonstrates the conversion is genuinely awkward.
- **O-P11 — the YAML subset boundary.** R-13's line is drawn where the security
  hazards are (anchors, tags, directives) and where the semantics are undefined
  (merge keys). **Recommendation: as stated.** Confirmed at cycle 0.8 against
  the yaml-test-suite's actual tag distribution — if the excluded constructs
  turn out to be a third of real-world YAML, the line moves and the decision is
  amended.
