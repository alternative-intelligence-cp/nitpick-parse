# The writers

Every format that reads also writes. The writer is not a convenience bolted on
at the end — it is **half of the oracle that judges the reader** (`TESTING.md`
§4), and it is why this library can make a stronger claim about its correctness
than a reader alone could.

---

## 1. Read implies write

**Rule W-1 (PA-060).** A format is not shipped until it can also write. The
writer lands in the same cycle as the reader, not later.

*Reasoning.* The round-trip property — parse, print, parse, and the two event
streams agree — is the strongest statement a parser can make about itself, and
it catches the class of bug a corpus does not: a reader that accepts a document
and *misunderstands* it produces a plausible tree, passes every "does it parse"
case, and only shows up when somebody prints it back and reads the difference.
The writer costs a few hundred lines and buys that.

---

## 2. The two writers per format

**Rule W-2.** Each format provides two entry points:

```nitpick
pub func:emit_json_doc    = NIL(Document->:d, Handle<Node>:root, EmitOpts:o, Bytes->:sink);
pub func:emit_json_events = NIL(...);   // an event sink, §5
```

The document writer is the ordinary one. The event writer exists so that a
streaming pipeline — read one format, write another, never build a tree — is
possible, and so that a 1 GB transcode does not need 1 GB of arena.

**Rule W-3 — the sink is a `Bytes`, not a `Writer`.** `nparse` performs no I/O
(`SAFETY.md` §2). A caller who wants bytes on a descriptor takes the `Bytes` and
writes it, or writes in chunks by draining it. Keeping the syscall out of the
library is what keeps it portable and testable.

**Rule W-4 — writing an explicit stack, like everything else** (PA-034,
`VALUE_MODEL.md` D-21). A document nested fifty thousand deep can be built by a
depth-bounded parser and would blow the stack in a recursive printer — the
subtlest form of the depth bug, arriving at the *end* of a successful parse.

---

## 3. Canonical form

**Rule W-5 (PA-061) — each format has exactly one canonical output form, it is
stated, and the writer is deterministic.** The same document produces the same
bytes, on every machine, forever.

| Format | Canonical form |
|---|---|
| JSON | no insignificant whitespace; `"` strings with the minimal escape set (control characters, `"`, `\`); numbers as the shortest round-tripping decimal; members in document order |
| TOML | tables in document order; bare keys where the grammar allows, basic strings otherwise; the shortest integer form in base 10; no blank lines inside a table |
| CSV | the dialect's delimiter and line ending; a field quoted iff it contains the delimiter, the quote, `\r` or `\n`; no trailing delimiter |
| YAML | block style; two-space indentation; plain scalars where resolution is unambiguous, single-quoted otherwise; no document markers unless the input had them |

**Rule W-6 — `EmitOpts` offers pretty-printing and it does not change the
canonical form.** Indentation, a trailing newline and key sorting are options; the
*canonical* form is the one the round-trip oracle uses and the one with no
options set. Two forms would mean two things to test.

**Rule W-7 — a number is written as the shortest decimal that reads back
identically.** For an `Int` node that is the digits; for a `Float` it is the
shortest round-tripping form, which the prelude's `flt64:ToString` already
computes (the compiler's D-193 shortest-round-trip Dragon4). `nparse` uses it
rather than writing a second one.

**Rule W-8 — `ND_BIG` writes its retained text verbatim.** A 40-digit integer
came in as text and goes out as the same text, which is the only way to round
trip it and the reason `VALUE_MODEL.md` D-19 keeps it.

**Rule W-9 — the escape set is minimal and stated.** JSON escapes `"`; `\`;
and `U+0000`…`U+001F` as `\u00XX` except `\b \f \n \r \t` which take their short
forms. It does **not** escape `/`, does not `\u`-escape non-ASCII, and does not
emit `\u` for anything above `U+001F`. Every one of those is a real
implementation divergence and each makes a byte-level round trip fail for no
reason.

---

## 4. The round-trip properties

**Rule W-10 (PA-062) — the property is a fixed point after one normalisation.**

```
parse(print(parse(b)))  ≡  parse(b)          for every b the format accepts
print(parse(print(d)))  ≡  print(d)          for every document d it can represent
```

Not `print(parse(b)) == b`: the input may have had whitespace, a different
escape spelling, or a non-canonical number, and a writer that reproduced them
byte for byte would be a formatter, not a writer. **One normalisation, then
stability** is the honest property and it is what the `roundtrip` stage asserts.

**Rule W-11 — the comparison is `doc_eq`, structural** (`VALUE_MODEL.md`
D-24), which is order-sensitive for maps because `nparse` preserves order
(D-9). A writer that reordered would fail the oracle, which is the point.

**Rule W-12 — every corpus case that parses is a round-trip case.** The
`roundtrip` stage runs over JSONTestSuite's `y_` set, toml-test's `valid/` set,
the CSV corpus and the YAML subset — so the oracle's coverage is the corpus's
coverage, for free, rather than a separate hand-written set.

**Rule W-13 — a cross-format round trip is a second, weaker property**, and it
is tested where it is meaningful: TOML's `valid/` set ships expected JSON, so
`parse TOML → print JSON → compare` is an oracle **independent of our own
reader** (`FORMATS.md` R-12). It is weaker because the formats' models differ —
TOML dates have no JSON representation — so it runs on the subset where the
models agree, and the subset is stated.

---

## 5. The event sink

**Rule W-14.** `emit_*_events` takes events one at a time and maintains its own
depth stack, mirroring the reader:

```nitpick
pub trait:EventSink = {
    func:put = NIL(Self->:self, Event:e, uint8[]:text);
    func:finish = NIL(Self->:self);
};
```

`text` is passed alongside because an `Event`'s `TextRef` is resolved against
its *parser* (`EVENT_MODEL.md` §5), and a sink has no parser. Resolving before
the call is the caller's one obligation and it is one line
(`event_text(p, e)`).

**Rule W-15 — a transcode is a loop, and it is the library's own best
example.** Read a format, write another, no tree:

```nitpick
while (true) {
    Step:s = r.step() ?! EParseState;
    pick (s) {
        (Step.Ev(e))    { drop w.put(e, event_text(@r, e)); },
        (Step.Fault(f)) { break; },
        (Step.Done)     { drop w.finish(); break; }
    }
}
```

Ten lines, constant memory, any format to any format. That is what the event
vocabulary is *for*, and it is why the tree is the layer above rather than the
only one.

**Rule W-16 — a sink refuses what its format cannot represent** with
`EParseEncode`: a NaN in JSON, a top-level scalar in TOML, a map key that is not
a string, a `Date` scalar in JSON. This is the second of the library's two error
identities (`SAFETY.md` §3) and it is a **caller** mistake — the caller chose
the target format — which is why it is an identity rather than a `Fault`.

---

## 6. Versioning the output

**Rule W-17.** The canonical form is part of the public interface: a change to
it changes every golden file and every consumer's stored output. It moves only
by a recorded decision, and it is a **minor** version (output changes, nothing
fails to compile) except where it changes what round-trips, which is major.

---

## 7. Open items

- **O-P12 — whether YAML's writer should emit flow style for short
  collections.** Block style everywhere is simpler, deterministic and ugly for
  `[1, 2, 3]`. **Recommendation:** block everywhere in the canonical form, flow
  as an `EmitOpts` option, decided at cycle 0.8 — the canonical form has one
  answer and the pretty printer can have taste.
