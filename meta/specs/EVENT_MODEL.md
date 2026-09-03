# The event contract

The interface the whole library is built around: what a parser produces, how a
caller drives it, and what a plugin owes. `PLUGIN_MODEL.md` states how a third
party implements it; this states what it *is*.

---

## 1. The shape

```nitpick
pub enum:Step = { Ev(Event); Fault(ParseError); Done; };

pub trait:Format = {
    func:step = Step(Self->:self);
};
```

A caller drives it:

```nitpick
JsonReader:r = json_reader(bytes);
while (true) {
    Step:s = r.step() ?! EParseState;
    pick (s) {
        (Step.Ev(e))    { /* handle */ },
        (Step.Fault(f)) { /* the compiler made you write this */ break; },
        (Step.Done)     { break; }
    }
}
```

**Rule E-1 (PA-020) — the parser is pull.** The caller asks for the next event.

*Reasoning, in order of weight.* **There are no closures** (D-018): a push
parser drives a visitor, and a visitor without captures is a trait object plus
a context struct hand-carried through every callback — which is what the
prototype's parser combinators became, and it is why they were unreadable.
**Pull composes**: a caller can stop, buffer, tee, or run two parsers in
lockstep, none of which a push parser permits without a state machine the caller
has to invent. **Pull is testable**: a test drives the parser one step at a time
and asserts on each, where a push parser must be given a recording visitor
before it can be observed at all.

**Rule E-2 (PA-023) — a syntax error is a value in the success channel.**
`Step.Fault` is not `Result.err`. `SAFETY.md` §3 has the full argument; the
short version is that `pick` exhaustiveness forces the caller to handle it,
where a `Result` could be `?|`-defaulted into silence or `?!`-trapped into a
crash.

**Rule E-3.** `step` returns `Result<Step>` and **fails only with
`EParseState`** — the API used out of order, or an incoherent option. No input
can make it fail.

**Rule E-4 (PA-024) — `step` is idempotent after `Done` and after `Fault`.**
Calling it again answers the same thing, forever. This removes the "used after
end" misuse case entirely rather than diagnosing it, which is why `EParseState`
has so little left to do.

---

## 2. `Event`

```nitpick
pub struct:Event = {
    EventKind:kind;     // 1 byte
    ScalarKind:scalar;  // 1 byte — meaningful only when kind is Scalar or Key
    uint8:flags;        // 1 byte — EV_ESCAPED, EV_BIG, EV_NEG, EV_EMPTY
    uint8:_pad;
    TextRef:text;       // 12 bytes — SCAN_MODEL.md §7
    Span:span;          // 8 bytes — the whole construct, for diagnostics
};                      // 24 bytes, align 4
```

```nitpick
pub enum:EventKind = {
    StartMap; EndMap;
    StartSeq; EndSeq;
    Key;
    Scalar;
    Comment;            // only when the format and options preserve them
    DocStart; DocEnd;   // multi-document formats; emitted once each otherwise
};

pub enum:ScalarKind = { Null; Bool; Int; Float; Str; Date; Time; DateTime; Raw; };
```

**Rule E-5 (PA-021) — `Event` has no owning field.** It is a plain 24-byte
value: it can be returned by value, stored in a `Vec`, compared, and copied.
`SAFETY.md` §6 has the two language rules that force this, and the second —
an arena `get` returns a *copy*, and a copy of an owning value is refused — is
the one that would bite hardest if it were ignored.

Scalar text is therefore a `TextRef`, never a `string`.

**Rule E-6 — `#size_of<Event>()` is asserted to be 24** by a probe and by a
unit test. A padding surprise changes the ring's memory budget and the
specification's number, and finding that out from a benchmark rather than from
a test is the wrong order.

**Rule E-7 — the vocabulary is closed at 1.0** (PA-025). Nine `EventKind`s and
nine `ScalarKind`s, and adding one is a minor version for readers (an
exhaustive `pick` over `EventKind` in a *consumer* would break, so it is
actually a major version — see `WRITER_MODEL.md` §6 and PA-009). XML would need
`Attribute` and mixed content, which is precisely why XML is out at 1.0
(`FORMATS.md` §5).

**Rule E-8 — the flags.**

| Flag | Meaning |
|---|---|
| `EV_ESCAPED` | the scalar's text is in the scratch because an escape was decoded |
| `EV_BIG` | a numeric scalar did not fit a 64-bit accumulator; the literal is still well-formed (`SCAN_MODEL.md` §6) |
| `EV_NEG` | a numeric scalar is negative — carried separately so `-0` survives |
| `EV_EMPTY` | the container that just started is empty; a hint, never load-bearing |

**Rule E-9 — `-0` survives.** `EV_NEG` with a zero magnitude is negative zero,
and a writer that emitted `0` for it would change the document. JSON and TOML
both distinguish it in `flt64`; the rule is stated because a naive `int64`
round trip loses it silently.

---

## 3. The grammar of a well-formed stream

**Rule E-10.** A conforming `Format` produces a stream matching:

```
stream  ::= DocStart doc DocEnd { DocStart doc DocEnd } Done
doc     ::= value
value   ::= Scalar
          | StartSeq { value } EndSeq
          | StartMap { Key value } EndMap
```

with `Comment` admissible anywhere a value may begin, and `Fault` admissible
anywhere at all — after which the stream ends.

**Rule E-11 — every `Start` has its `End`, unless a `Fault` intervened.** A
parser that returns `Fault` is not required to close its open containers, and a
consumer must not assume balance after one. The tree builder unwinds its own
stack on a `Fault` rather than waiting for `End` events that will not come.

**Rule E-12 — `Key` is always followed by exactly one value** (which may itself
be a container). A format with keyless entries (a CSV row) emits a sequence,
not a map.

**Rule E-13 — the grammar is checked, not assumed.** `event_validate` is a
wrapper `Format` that sits over any other and asserts E-10 through E-12 on
every step, failing loudly on a violation. It runs over every plugin in the
conformance suite (`PLUGIN_MODEL.md` §5), and a third-party format is expected
to be developed with it wrapped on. It is not on in production, because it
costs a state machine per step and the shipped formats are proven.

---

## 4. Depth

**Rule E-14 (PA-022) — nesting is an explicit stack**, `Vec<Frame>`, owned by
the parser, and there is **no native recursion anywhere on an input-controlled
path** — not in the parser, not in the builder, not in the writer, not in the
tree walk, not in comparison, not in the drop.

```nitpick
pub struct:Frame = { EventKind:kind; uint32:count; Span:span; };
```

`SAFETY.md` §5 has the reasoning: the language has no stack-depth guard, so a
recursive descent on `[[[[[…` is an uncontrolled fault, which is the one failure
mode this ecosystem exists to make impossible.

**Rule E-15.** Exceeding `NPARSE_MAX_DEPTH` is `Fault(DepthExceeded)` with the
span of the container that would have been opened. The default is 128
(`SAFETY.md` §7) and it is a per-parse option.

**Rule E-16 — the depth stack is preallocated to the bound.** `NPARSE_MAX_DEPTH`
frames of 16 bytes is 2 KiB; allocating it once at `reset` removes a growth path
from the hot loop and makes the parser's total allocation a stated constant plus
the scratch.

---

## 5. Lifetimes — the one rule a caller must know

**Rule E-17.** An `Event`'s `TextRef` is valid **until the next `step`**.

- When `text.src` is `Input`, it points into the caller's bytes and is valid as
  long as those are.
- When `text.src` is `Scratch`, it points into the parser's scratch, which the
  next `step` clears.

`event_text(p, e) -> uint8[]` resolves a `TextRef` against a parser and returns
a borrow. Because it is a borrow (D-004), the compiler will not let a caller
store it past the call — so the hazard is confined to a caller who *copies* the
bytes out into their own storage and then keeps the parser alive, which is
correct, or who copies the `TextRef` itself and resolves it later, which is
not.

**Rule E-18 — the safe path is the `Document`.** `doc_build` copies every
scalar into the document's pool, so a caller who does not want to think about
E-17 uses the tree and never sees a `TextRef`. This is why the streaming API is
the *lower* layer rather than the only one.

**Rule E-19 — a `TextRef` carries no parser identity**, and resolving one
against the wrong parser is a caller mistake `EParseState` does not catch. It
is stated here, tested by a rejection case that shows the compiler catching the
*borrow* form of the mistake, and mitigated by E-18.

---

## 6. Options

**Rule E-20.** Every parser takes an options value at construction, and every
field has a stated default:

```nitpick
pub struct:Options = {
    uint32:max_depth;        // NPARSE_MAX_DEPTH
    uint32:max_scalar;       // NPARSE_MAX_SCALAR
    uint32:max_key;          // NPARSE_MAX_KEY
    uint32:max_errors;       // NPARSE_MAX_ERRORS; 0 = stop at the first
    DupPolicy:dup_keys;      // Error (default) | First | Last
    bool:keep_comments;      // false
    bool:allow_bom;          // true — strip a leading U+FEFF
};
pub func:options_default = Options() never fails;
```

**Rule E-21 — an incoherent option is `EParseState` at construction**, not a
surprise at step 4000: `max_depth == 0`, `max_scalar == 0`, a CSV dialect whose
delimiter equals its quote. Checking at construction is what lets every later
`step` be total.

**Rule E-22 — options are per parse, never global.** There is no module-level
configuration, which is not a preference: D-211 refuses a mutable module
binding, and a `fixed` one could not be changed anyway.

---

## 7. Streaming

**Rule E-23 — the whole input is present.** At 1.0 a parser is constructed over
a complete `uint8[]`. It does not consume a `Reader` and does not ask for more
bytes.

*Reasoning.* A chunked parser must be able to suspend mid-token, which means
every scanning function becomes a resumable state machine — a large complication
for a case the library can serve two simpler ways: a caller who can afford the
memory hands over the whole buffer, and a caller who cannot uses a
**record-oriented** format (CSV, and JSON Lines) where the caller splits on the
record boundary and parses each record whole.

**Rule E-24.** Cycle 0.10 revisits this with a measurement rather than a guess:
whether a genuinely incremental `feed(bytes)` is needed is answered by the
dogfood consumer (cycle 0.12) and by whether anyone asks. The event stream's
shape does not change either way — a chunked parser produces the same events —
so this is an implementation question, not a contract question, and the
contract is what this document freezes.

**Rule E-25 — a 1 GB input is a supported case today**, without chunking:
nothing proportional to the input is copied (`SCAN_MODEL.md` §7), so the
memory cost is the input the caller already has plus a bounded scratch. Cycle
0.10's gate is exactly this measurement.

---

## 8. Open items

- **O-P5 — whether `Comment` should carry its *position relative to* the
  construct it annotates** (leading, trailing, own-line). A formatter needs it;
  a data consumer does not. **Recommendation:** not at 1.0 — `keep_comments`
  gives the span, and a formatter can derive the relation from the spans it
  already has. Revisit if a formatter is written against the library.
- **O-P6 — incremental feeding.** See E-24. **Open by design:** it is a
  *measurement*, taken at cycle 0.10, and the contract does not depend on the
  answer.
