# Plugins

What a plugin is in a language with no dynamic loading, what it owes, and how a
third party writes one.

---

## 1. What "plugin" can and cannot mean here

**Rule G-1 (PA-070) — a plugin is a `Format` trait implementation. There is no
registry, no dynamic loading, and no macro.**

The constraint is absolute and worth stating plainly, because "plugin" implies
something in most ecosystems that is unavailable in this one:

- **There is no `dlopen`.** Loading code at run time means an FFI boundary, and
  **in-process FFI does not exist in Nitpick** (D-149). The link is
  closed-world by construction (`BUILD.md` §2) and there is no flag to relax it.
- **There is no plugin ABI**, because there is no way to load a plugin across
  one.
- **A plugin is therefore compiled into the program that uses it.** The
  application decides, at its own compile time, which formats it wants.

That is less dynamic than a JVM's service loader and is exactly as dynamic as
Rust's `serde`, which is the comparison that matters: extensibility here means
*anyone can write one and everything downstream works on it*, not *it can be
dropped into a running process*.

**Rule G-2 — the out-of-process form is real and is not this.** A driver over
the compiler's Bridge (D-149) genuinely could host a foreign parser in another
process. It is enormous — a wire protocol, a supervised child, a deadline on
every dispatch — and it buys nothing for a parser, whose input and output are
both already in the caller's memory. It is recorded here as considered and
declined, so nobody re-derives it.

---

## 2. The interface, in full

A plugin implements one trait:

```nitpick
pub trait:Format = {
    func:step = Step(Self->:self);
};
```

and provides one bare constructor function, because **the language has no static
methods** (D-185):

```nitpick
pub func:json_reader = JsonReader(uint8[]:src, Options:opt);
```

That is the whole required surface. Everything else the library offers —
`doc_build`, `event_validate`, the writers, the fuzzer harness, the query API —
is written against `Format` and works on a third-party implementation with no
registration, no annotation and no change.

**Rule G-3 — `Self->` receiver, not by value.** A by-value receiver would
consume the parser per call (D-183). Every method takes `Self->`.

**Rule G-4 (PA-071) — `dyn Format` is object-safe, and it is the runtime-choice
path.** `step` takes a `Self->` receiver, returns no `Self`, mentions no
associated type and has no type parameters, so the trait satisfies the object
safety rules (`TRAITS_REFERENCE.md` §4.2). An application that must choose a
format from a file extension holds a `dyn Format`.

Static dispatch through a bound — `func:consume<F: Format> = …` — is the
intended path and is what every example uses. `dyn` costs an indirect call per
event and exists so that "choose at run time" does not require a hand-written
`pick` in every consumer.

**Rule G-5 — format dispatch is the application's `pick`, and the library ships
one convenience.** `builtin_open(kind, src, opt) -> dyn Format` covers the four
shipped formats over a `BuiltinFormat` enum. A third-party format is not in it
and does not need to be: the application that knows about the format writes the
one `pick` arm that constructs it. **A registry would need a mutable
module-level table, which D-211 refuses**, and a `fixed` one could not be
extended by a consumer — so the thing that looks like the obvious design is not
merely inadvisable here, it is unspellable.

---

## 3. What a plugin owes

**Rule G-6 — the contract, enumerated.** A conforming `Format`:

1. produces a stream matching the grammar in `EVENT_MODEL.md` §3;
2. **never traps**, on any input, for any reason — which in practice means it
   uses `src/scan/arith.npk` for every accumulation (`SCAN_MODEL.md` §5) and an
   explicit stack for every nesting (`EVENT_MODEL.md` §4);
3. **never fails except with `EParseState`**, and only for a caller mistake;
4. is **idempotent after `Done` and after `Fault`** (E-4);
5. **consumes every byte exactly once** — the sum of the spans it reports, plus
   the bytes it deliberately skips, equals the input;
6. **allocates only into its own scratch**, bounded by `NPARSE_MAX_SCALAR`, and
   copies nothing proportional to the input into anything else;
7. **terminates**: every `step` either advances the cursor or returns `Done` or
   `Fault`, and a `step` that returns `Ev` without advancing is a defect the
   conformance harness catches;
8. reports a **span for every event** that is within the input and whose `lo`
   is not greater than its `hi`.

**Rule G-7 — a plugin declares no `error:` of its own.** `EParseState` is
`nparse`'s and is the only identity a format may raise. A plugin that wanted a
new one would be adding a `failsafe` arm to every consuming program
(`SAFETY.md` §3), which is not a format's decision to make. A format-specific
condition is a `ParseError` code (`DIAGNOSTIC_MODEL.md` §3), and the code enum
has a reserved range for third-party formats.

---

## 4. Writing one

The shape, in full, for a reader who wants the minimum:

```nitpick
mod:mini;
use "../event/event.npk".*;
use "../scan/cursor.npk".*;

pub struct:MiniReader = {
    Cursor:cur;
    Vec<Frame>:depth;
    Bytes:scratch;
    Options:opt;
    uint8:state;
};

pub func:mini_reader = MiniReader(uint8[]:src, Options:opt) { … };

impl:MiniReader:Format = {
    func:step = Step(MiniReader->:self) { … };
};
```

and a consumer uses it exactly as it uses `json_reader`:

```nitpick
MiniReader:r = mini_reader(bytes, options_default());
Document:d = doc_build(@r) ?! EParseState;
```

**Rule G-8 — nothing in `doc`, `emit` or the harness knows the shipped formats
are special.** The four in `src/format/` import nothing the library does not
export, use no privileged entry point, and are exercised by the same
conformance harness a third party would use. That is the test of the claim, and
`TESTING.md` §5 makes it one: the harness runs its plugin conformance suite over
a **deliberately trivial** fifth format that lives in `tests/`, so the path a
third party takes is walked on every run.

---

## 5. The plugin conformance harness

**Rule G-9.** `plugin_conform<F: Format>(make, corpus)` drives an
implementation over a corpus and asserts G-6's eight obligations, mechanically:

| Obligation | How it is checked |
|---|---|
| grammar | `event_validate` wrapped over the parser (E-13) |
| never traps | the case runs to completion; a trap is a non-zero exit the harness reports |
| never fails but `EParseState` | any other `Result.err` fails the case |
| idempotent | `step` called three more times after `Done`/`Fault`, same answer |
| consumes every byte | span coverage summed and compared to the input length |
| bounded allocation | the scratch's high-water mark asserted under the bound |
| terminates | a step counter bounded at `4 × input length`; exceeding it fails |
| spans valid | every event's span checked in range and ordered |

**Rule G-10 — every shipped format runs the conformance harness over its own
corpus on every full run**, and so does the trivial test format. A plugin
author runs the same function.

---

## 6. Versioning the interface

**Rule G-11.** `Format`, `Step`, `Event`, `EventKind`, `ScalarKind`, `TextRef`
and `Options` are the plugin ABI in the only sense this language has one:
**source compatibility**. Adding an `EventKind` breaks every consumer's
exhaustive `pick`, so it is a **major** version (PA-009). Adding an `Options`
field is a minor version, because a struct literal that omits a field is
refused — so the constructor `options_default()` is the compatible path and is
what every example uses.

**Rule G-12 — `options_default()` exists precisely because struct literals must
be complete.** `Default` is not derivable (D-123) and a struct literal that
omits a field is a compile error, so a caller who wrote `Options{ … }` by hand
would break on every added field. The documented spelling is
`Options:o = options_default(); o.max_depth = 64u32;`.

---

## 7. What this library is not, and what would be

**Rule G-13 (PA-007) — `nparse` is a data-format library, not a compiler front
end.** It produces a *value* stream, not a lossless concrete syntax tree; it
does not preserve every byte of whitespace; it does not support incremental
reparse; and it has no notion of a token that is invalid-but-retained.

The prototype's `nparse` was the other thing: red/green trees, parser
combinators, Pratt parsing, error-tolerant recovery, an LSP backend. Both are
legitimate libraries and they share almost nothing — a CST keeps trivia and
tolerates every error because an editor needs the tree of a broken file, where a
data-format reader wants a value or a fault. **The user's brief asked for the
second**, and building both behind one name is how a library ends up serving
neither.

If the first is wanted later it is a **separate library** — the natural name
being `nitpick-cst` — and it can reasonably use `src/scan/` from here, at which
point the dependency question is a real one and gets a real answer.

---

## 8. Open items

- **O-P7 — the reserved `ParseError` code range for third-party formats.** The
  enum is closed (`DIAGNOSTIC_MODEL.md` §3), so a third-party format needs
  either a reserved band or a generic `FormatSpecific(uint16)` variant.
  **Recommendation:** `FormatSpecific(uint16)` plus a `format_code_text`
  callback-free rendering hook, because a reserved band in a closed enum is a
  band somebody eventually collides in. Decided at cycle 0.9 with the
  diagnostic work.
