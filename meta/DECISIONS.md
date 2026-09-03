# Design decisions

Every settled design decision for `nparse`, with the reasoning, the
alternatives that were considered, and the date. **This is the file to read
when something in the specifications looks unusual**, because it is recorded
why.

Referenced as `PA-nnn` from the specifications. `D-nnn` in those documents
refers to the **compiler's** `meta/specs/DECISIONS.md`; those are language
decisions and are not ours to amend.

**Rule: a settled decision's text is never rewritten.** A decision that turns
out to be wrong is superseded by a new one that says so and says why; the old
text stays, dated, because it records what was true when it was made. This is
the compiler's D-085/D-202 pattern.

**Numbering is allocation order, grouped by the batch that settled it.**
PA-001…PA-083 are the founding batch, written with the specification set and
organised below by area. Later batches are appended whole with their own
heading, because a batch ratified together is a unit.

---

## Foundations

### PA-001 — the library is `nparse`; the repository is `nitpick-parse`
**2026-09-03.** The module prefix, every public symbol's prefix, and the
eventual package name are `nparse`, matching the ecosystem's `n`-prefix
convention (`nfs`, `nproc`, `nio`, `nvec`, `nsys`, `ntui`) and the name the
project's author already used in `.internal/idea.txt`. The repository keeps the
longer name because a repository name is a search term and `nparse` alone is
not one.

*Alternatives:* `parse` (collides with a user's own module of that name and
breaks the convention every other library follows); `nitpick_parse` (verbose at
every import site).

### PA-002 — the specifications are the authority
**2026-09-03.** Code that disagrees with `meta/specs/` is a defect in the code.
A specification that is wrong is amended by a decision recorded here, never by
editing the text and moving on. The compiler's own cycle notes record the same
finding repeatedly — the compiler and the thing that describes it have to be
diffed, because reading either alone never reveals the gap — and
`TESTING.md` §3's checks are that diff, applied here.

### PA-003 — `harness/` builds and tests `nparse` until `npkg` can
**2026-09-03.** Measured at the compiler's 1.5.0: `npkg build` is the
compiler's own bootstrap ladder with no generic-project path, and
`[dependencies]` is parsed but the loader's dependency-root list is created
empty and never populated, so cross-repository imports do not resolve. A Python
harness drives `npkc`, `llc` and `ld.lld` directly, mirroring
`bootstrap/harness/`'s relationship to `npkg`, and retires the same way — both
running side by side with a parity check before the older is removed.

*Not a dependency violation:* zero-dependency governs the artifact, not the
workbench (the compiler's `ORCHESTRATION.md` §6 says so in as many words).

### PA-004 — `nparse` declares its own storage primitives
**2026-09-03.** `Vec<T>`, `Bytes` and `SmallMap<K, V>` live in `src/core/` and
are ours, alongside `limits.npk` — every named bound in the library, in one
file, because a bound scattered across call sites is a bound nobody can audit.
The compiler's `List<T>` is not imported: it is a compiler internal whose own
header says it exists for the compiler's tables, and reaching into another
project's `src/` couples this library's correctness to a file that is not a
published interface. `Vec<T>` is `List<T>`'s shape, deliberately, because that
shape is right and has been exercised across twenty-two families.

### PA-005 — no dependencies, and `[dependencies]` stays empty
**2026-09-03.** The language and its prelude, and nothing else. Including, by
name: not the compiler's `src/`, not the compiler's `lib/` (scheduled to move
to an `nlibc` sibling), not `nregex`, not `ntime`.

*`nregex` specifically:* a parser that needed a regex engine to tokenize would
be a parser that had stopped being a parser. Every format here is scannable by
a hand-written cursor, which is faster, smaller and provable. The prototype's
`nparse` did wire a Thompson NFA in as a modal lexer backend — which was right
for the general *language* front end it was trying to be, and is wrong for this
one (PA-007).

*`ntime` specifically:* TOML has four date-time types and `ntime` will one day
own them. The overlap is real and is recorded as O-P4, not resolved by a
dependency that cannot resolve.

### PA-006 — `nparse` makes no syscall, and is therefore not platform-bound
**2026-09-03.** It reads no file, opens no descriptor, spawns no process,
installs no signal handler, and touches no device. The caller hands it bytes.

*Consequences worth stating, because they remove hazards the rest of the
ecosystem carries:* there is no trap path to protect and so no restore record;
there is no concurrency, no `await`, and no deadline discipline; there is no
clock and no environment, so the same input produces the same output on every
machine forever — which is what makes the round-trip oracle a fact rather than
an approximation. And **nothing in this library is Linux-specific or
x86-64-specific**, which is not true of `ntui`, `nsockets` or `ntime`.

*Alternative declined:* a `parse_file(Path)` convenience. It would pull in the
syscall surface, a descriptor lifetime, an error class and a platform, to save
a caller one line of `read_file`.

### PA-007 — `nparse` is a data-format library, not a compiler front end
**2026-09-03.** It produces a *value* stream, not a lossless concrete syntax
tree. It does not preserve every byte of trivia, does not support incremental
reparse, and has no notion of a token that is invalid-but-retained.

*Reasoning.* The prototype's `nparse` was the other thing — red/green trees,
parser combinators, Pratt parsing, error-tolerant recovery, an LSP backend —
and the two share almost nothing. A CST keeps trivia and tolerates every error
because an editor needs the tree of a broken file; a data-format reader wants a
value or a fault. The project author's brief asked for the second ("so for
instance maybe we ship csv, toml, yaml, and json plugins"), and building both
behind one name is how a library ends up serving neither.

*Not foreclosed:* if the first is wanted it is a separate library, the natural
name being `nitpick-cst`, and it can reasonably use `src/scan/` from here — at
which point the dependency question is a real one and gets a real answer.

### PA-008 — the error budget is TWO, and no input can produce either
**2026-09-03.** `nparse` declares exactly `EParseState` (the API used out of
order, or an incoherent option) and `EParseEncode` (a `Document` the target
format cannot represent). **Both are caller mistakes. Neither is reachable from
any byte stream.**

Every condition an input can cause is a `Fault(ParseError)` value carried in
the **success** channel of `Step`.

*Reasoning.* REACH-002 makes every `error:` that can reach `failsafe` a named
arm every consuming program must carry, and an unhandled one stops the process.
For a library whose entire job is reading bytes somebody else controls, routing
malformed input through that channel would mean **a bad byte can stop a
program** — which is the failure mode this whole ecosystem exists to prevent,
arriving through the front door.

*And the value channel is stronger, not weaker.* A caller handed a `Result` can
write `?| default` and silently swallow a malformed document, or `?!` and turn
it into a trap. A caller handed a `Step` **must write a `Fault` arm**, because
the compiler refuses a non-exhaustive `pick`. The language's own exhaustiveness
rule does the work an error identity would only pretend to do.

*Alternatives declined:* one identity per fault class (thirty-odd arms in every
consumer, and the language would enforce them); one identity `EParse` with the
detail in a field the caller reads out of band (the out-of-band read is exactly
what D-069 removed from `Result`, and a caller can still ignore it).

### PA-009 — versioning, and adding an error identity or an enum variant is MAJOR
**2026-09-03.** `0.x` until the compiler reaches 1.0 and the API has survived
cycle 0.12's application; semantic versioning thereafter.

**Three things are major changes, and two of them are unusual:**

- **adding a public `error:` identity** — REACH-002 makes it a new mandatory
  `failsafe` arm in every consumer, a compiler-enforced source break;
- **adding an `EventKind`, a `ScalarKind`, a `NodeKind` or a `FaultCode`
  variant** — a consumer's exhaustive `pick` stops compiling;
- removing or renaming any public name, as usual.

That first pair is the practical teeth behind PA-008's budget of two and behind
`EVENT_MODEL.md` E-7's closed vocabulary: neither is a style guide, they are
what keeps the major version from moving.

*Adding an `Options` field is minor*, because a struct literal that omits a
field is refused and `options_default()` is therefore the documented spelling
(PA-025's corollary, `PLUGIN_MODEL.md` G-12).

---

## Scanning

### PA-010 — the caller owns the input, and `nparse` never reads a file
**2026-09-03.** There is no `parse_file`. A caller who has a path reads it with
the prelude's `read_file` and hands the bytes over. This is what keeps the
library free of syscalls (PA-006), free of a descriptor lifetime, and testable
from a byte literal.

### PA-011 — a span is byte offsets; line and column are computed on demand
**2026-09-03.** Nothing tracks a line counter while scanning.

*Reasoning.* A line/column pair maintained per byte costs a branch on every
byte of every parse to serve a case that arises once per *error*, and errors
are rare. `scan_line_col(src, offset)` counts newlines from the start when a
diagnostic is rendered — for a 1 GB input with one error, one extra pass, once,
on the path where a human is already reading a message.

*Alternative declined:* a line-start index built during the parse. It is the
right answer for a document with a thousand errors and the wrong one for the
99% case; it is recorded as O-P3 and is a *measurement*, taken when recovery
makes many-error documents real.

### PA-012 — no arithmetic in this library may trap on any input
**2026-09-03.** **The library's central correctness claim.**

Plain integer overflow *traps* in Nitpick (D-210), so the ordinary decimal
accumulator —

```nitpick
acc = acc * 10i64 + d;      // WRONG
```

— crashes the process on `99999999999999999999999`, twenty-three digits anyone
can type into a JSON field. **That is a remote denial of service in the three
most obvious lines in the library.** No other language's parser has this
failure, because no other language traps here: a C parser wraps, a Rust parser
wraps in release. In Nitpick it stops the program.

Every accumulation is therefore range-checked *before* the operation that could
overflow, through three helpers in `src/scan/arith.npk` that are the **only**
places the library multiplies or adds an input-derived value. The answer on
overflow is a `Fault(NumberOutOfRange)`, never a trap and never a wrap.

`SCAN_MODEL.md` C-14 enumerates every site; `TESTING.md` §3's
`check_no_raw_accumulate` greps for the shape that would violate it; and
`VERIFICATION.md` §4 makes the helper's four internal facts the highest-value
proof obligations in the library.

*Alternative declined:* accumulating in `int256` and narrowing at the end. It
moves the trap rather than removing it (`int256` overflows too, just later), it
costs a wide multiply per digit, and it does not help the exponent, the
codepoint or the length accumulations.

### PA-013 — UTF-8 validation is explicit and per-format
**2026-09-03.** `nparse` does not assume the input is UTF-8 and does not
validate it globally. JSON requires it and validates (RFC 8259 §8.1); CSV does
not and passes bytes through; TOML requires it for strings and keys; YAML
requires it.

*Reasoning.* A CSV file in Latin-1 exported from a spreadsheet is a real thing a
caller hands you, and a library that refused it would be wrong. A JSON document
that is not UTF-8 is malformed and accepting it is a vulnerability. The two
answers differ, so the decision belongs to the format.

### PA-014 — escapes go to scratch; the common case copies nothing
**2026-09-03.** A scalar with no escape sequence is a `TextRef` into the
caller's input. Only a scalar that *contains* an escape is rewritten, into the
parser's scratch, and its `TextRef` points there instead. The scratch is cleared
per scalar, which is what makes its lifetime one event
(`EVENT_MODEL.md` §5).

---

## The event contract

### PA-020 — the parser is PULL, not push
**2026-09-03.** The caller asks for the next event.

*Reasoning, in order of weight.* **There are no closures** (D-018): a push
parser drives a visitor, and a visitor without captures is a trait object plus a
context struct hand-carried through every callback — which is what the
prototype's parser combinators became and why they were unreadable. **Pull
composes**: a caller can stop, buffer, tee, or run two parsers in lockstep, none
of which a push parser permits without a state machine the caller has to invent.
**Pull is testable**: a test drives one step at a time and asserts on each, where
a push parser must be given a recording visitor before it can be observed at
all.

### PA-021 — `Event` is POD; scalar text is a `TextRef`, never an owned string
**2026-09-03.** A plain 24-byte value with no owning field, so it returns by
value, sits in a `Vec`, compares and copies.

*Two language rules force it, and the second is the sharper one:* an owning
field makes the type move-only (TYPE-046), so a `Vec` of them could not be
copied or cleared; and **an arena `get` returns a copy** (D-152), and a copy of
an owning value is *refused* — so the same shape in a `Node` could not be read
back at all.

### PA-022 — nesting is an explicit stack; there is no native recursion
**2026-09-03.** Not in the parsers, not in the tree builder, not in the writers,
not in the comparison, not in the walk, not in the drop.

*Reasoning.* `[[[[[[[[…` repeated fifty thousand times is eight bytes of shell
and a stack overflow in a recursive-descent parser. The language has **no
stack-depth guard** — `stack-depth` is an obligation kind scheduled for the
compiler's 1.5.8 (`VERIFICATION_REFERENCE.md` §365) and does not exist today —
so the overflow is a raw fault, not a controlled stop.

*The subtle half:* a document built by a depth-bounded parser and then freed by
a *recursive drop* is a stack overflow at the end of a **successful** parse.
That is the form of this bug most likely to survive review, which is why the
rule names the walk, the compare, the print and the drop explicitly.

### PA-023 — a syntax error is a value in the success channel
**2026-09-03.** `Step = { Ev(Event); Fault(ParseError); Done; }`. `Step.Fault`
is not `Result.err`. See PA-008 for the full argument.

### PA-024 — `step` is idempotent after `Done` and after `Fault`
**2026-09-03.** Calling it again answers the same thing, forever. This removes
the "used after end" misuse case entirely rather than diagnosing it, which is
why `EParseState` has so little left to do — and a smaller error surface is the
point of PA-008.

### PA-025 — the event vocabulary is closed at 1.0
**2026-09-03.** Nine `EventKind`s and nine `ScalarKind`s. Adding one is a major
version (PA-009) because a consumer's exhaustive `pick` stops compiling.

*The concrete consequence:* XML would need `Attribute` and a mixed-content
notion, so **adding XML later is a breaking change however it is done** — which
is half the reason XML is out at 1.0 (PA-052) rather than added badly now to
avoid one.

---

## The document model

### PA-030 — the tree is an arena of POD nodes with a side string pool
**2026-09-03.** Not a linked structure of owning values.

*The forcing rule, stated precisely because it surprises people:* an arena
`get` returns a **copy** (D-152), and a copy of an owning value is **refused**
(TYPE-046). A node holding a `string` could therefore not be read back at all —
not "would be slow", not "would allocate": `doc.nodes.get(h)` would not
compile. Text lives in the pool and a node addresses it by offset and length.

*What the arena buys:* a `Handle<Node>` carries a generation, so a handle that
outlived its slot fails `get` with `StaleHandle` (−4106) rather than reading
freed memory — the use-after-free class closed structurally.

### PA-031 — maps preserve insertion order
**2026-09-03.** A `Map` node's chain is in the order the input presented the
pairs, and a writer emits them in that order.

*Reasoning.* TOML and YAML have constructs whose meaning depends on order. JSON
does not require it, but every JSON tool that reorders keys makes every diff of
every configuration file useless — a cost paid by humans forever to save a hash
table. Preserving order is strictly more information and a caller who does not
care simply does not look.

*Cost accepted:* lookup is a linear scan, and `doc_index` (PA-030's neighbour,
`VALUE_MODEL.md` D-13) is the explicit opt-in for a caller doing thousands.

### PA-032 — duplicate keys are a fault by default, with a policy
**2026-09-03.** A repeated key in one map is `Fault(DuplicateKey)` carrying the
span of the **second** occurrence, unless `DupPolicy` says `First` or `Last`.

*Reasoning.* Duplicate-key handling is a documented source of parser
differentials: two implementations disagree about which value wins, a validator
checks one and a consumer reads the other, and the disagreement is the
vulnerability. The formats do not agree either — **TOML forbids duplicates,
YAML forbids them, and JSON leaves the behaviour undefined** (RFC 8259 §4). An
error by default is the only choice right for two of the three and safe for the
third.

*And the policy does not relax a format that forbids them.* TOML and YAML do
not become permissive because a caller asked; the option changes JSON's
behaviour and nothing else, and that is stated so nobody expects otherwise.

### PA-033 — numbers stay text until the caller chooses a type
**2026-09-03.** The scanner **classifies** a numeric literal and records its
span; it does not decide what type it is. `EV_BIG` / `ND_BIG` means "did not fit
a 64-bit accumulator" and the literal's text is retained.

*Reasoning.* JSON's grammar admits arbitrary-precision decimals and every
implementation quietly picks IEEE-754 double; TOML specifies `int64` and
`flt64` exactly; CSV has no types at all. A library that picked one
representation would be wrong for two of the three. Nitpick has `int256` and
`frac64` for the callers who need them, and a library that had already narrowed
to `int64` would have destroyed the information before the caller could ask.

*The one place `nparse` is knowingly inexact* is `num_flt64`, which produces the
nearest `flt64` ties-to-even; `num_text` is always available for a caller who
cannot accept that.

### PA-034 — building, walking, comparing, printing and dropping use explicit stacks
**2026-09-03.** The corollary of PA-022 applied to the tree. Named separately
because the parser's stack is the one people remember and the drop's is the one
they forget.

---

## Diagnostics

### PA-040 — one `ParseError` value with a closed code enum
**2026-09-03.** A plain 24-byte value: a `FaultCode`, flags, a span, an
`expected` bitmask, what was found, and the depth. No owning field, so it rides
inside `Step.Fault`, sits in a `Vec` when recovery collects several, and copies
freely.

*The enum is closed and adding a variant is a major version* (PA-009).
`FormatSpecific` exists so a third-party format never needs one.

*One compromise, recorded as one:* `found` holds a byte for `UnexpectedByte`
and a token class otherwise. Two meanings in one field is the shape D-069
removed from `Result`, so the accessor pair `fault_found_byte` /
`fault_found_class` is the only way to read it — which is what the D-069
objection was actually about. The alternative is two fields and 28 bytes.

### PA-041 — rendering is a function, not a format string
**2026-09-03.** No message text is stored in `ParseError`.

*Reasoning.* Nitpick has **no format-specifier language** (D-053): `printf` and
its relatives do not exist and there is nothing for a template to be
interpreted by. Rendering as a function keeps messages free to improve, makes
translation possible, and keeps the struct at 24 bytes with no owning field.
The code `NPARSE-nnnn` is stable and the prose after it is not — the compiler's
own rule, for the same reason.

*One limitation stated rather than mitigated:* the caret line counts
**codepoints, not display columns**, because `nparse` carries no Unicode width
tables and will not — that is `ntui`'s domain and two copies would be two
things to keep in sync. A consumer with width tables renders its own caret from
the span, which is why the span is what the library guarantees.

### PA-042 — recovery is opt-in, bounded, and per format
**2026-09-03.** With `max_errors == 0` (the default) the first fault ends the
parse. With a positive value the parser resynchronises and continues, collecting
up to that many.

*There is no format-neutral resynchronisation rule*, so each format states its
own. **Recovery never invents structure** — no fabricated closing brace — and a
recovered parse is **not** re-printable, so the round-trip oracle does not run
on one. Recovery serves a *diagnostic* consumer such as a linter, not a data
consumer, and `doc_build` returns the fault regardless.

---

## The formats

### PA-050 — the 1.0 set is JSON, TOML, CSV and a defined YAML subset
**2026-09-03.** Four formats, each a cycle, each with a vendored conformance
corpus as its gate. The set is closed for the 1.0 release: adding a fifth before
it would mean four formats tested and one asserted.

### PA-051 — the YAML subset, stated construct by construct
**2026-09-03.** **In:** block and flow collections, plain/single/double-quoted
scalars, literal and folded block scalars with chomping and indentation
indicators, comments, the core schema's resolution, document markers with
exactly one document. **Out**, each reporting `Fault(Unsupported)` naming the
construct: anchors and aliases, merge keys, tags beyond the core schema,
directives, multiple documents, complex mapping keys.

*Reasoning.* Anchors are the **billion-laughs amplification vector**; a bounded
implementation needs an expansion budget, a cycle detector and size accounting
the rest of the library does not have. Merge keys are a convention YAML 1.2
does not define. Tags are a type system.

**The subset is a decision, not a stage of completion.** Full YAML is cycle 1.1
post-1.0, with anchors carrying an expansion budget as a first-class part of the
design. Shipping a "YAML parser" that silently *ignored* anchors would be worse
than one that refuses them by name — which is why `Unsupported` is a distinct
code from `UnexpectedByte`.

### PA-052 — XML is out at 1.0
**2026-09-03.** Recorded as a decision rather than an omission.

*Reasoning.* XML's data model is genuinely different — attributes are not
children, mixed content interleaves text and elements, namespaces rewrite names
— so the event vocabulary would need `Attribute` and a text-run notion, which is
a major version of the plugin interface (PA-025). Adding XML is therefore a
breaking change however it is done, and doing it badly now to avoid one is the
worst of both. Entities and DTDs are also the same amplification hazard as YAML
anchors with thirty years more surface.

### PA-053 — a format's gate is its published conformance corpus
**2026-09-03.** A claim in `FORMATS.md` means there is a vendored corpus behind
it and every case is judged: JSONTestSuite for JSON, toml-test for TOML, the
yaml-test-suite filtered to the subset for YAML, and a hand-built corpus plus
the W3C CSVW cases for CSV.

*Hand-written cases test the rules the author understood* — the compiler's
`GraphemeBreakTest.txt` lesson, applied. **The expected pass count is exact and
an unexpected improvement fails the run**, because a count that went up usually
means a case was reclassified or a fault was silently downgraded to acceptance.

*CSV's gate is the weakest of the four* because CSV has the weakest
specification, and that is stated rather than hidden; its hand-built corpus is
correspondingly larger.

### PA-054 — the specification version is pinned and recorded
**2026-09-03.** In `meta/research/format-versions.md`, with the document's own
version string and the date it was read. "TOML" without a version is three
incompatible languages.

---

## The writers

### PA-060 — every format that reads also writes, in the same cycle
**2026-09-03.** The writer is not a convenience bolted on at the end: it is
**half of the oracle that judges the reader**.

*Reasoning.* A reader that *accepts* a document and misunderstands it produces a
plausible tree, passes every "does it parse" case in the corpus, and shows up
only when somebody prints it back. The writer costs a few hundred lines and
buys the strongest statement a parser can make about itself.

### PA-061 — one canonical form per format, deterministic
**2026-09-03.** The same document produces the same bytes on every machine
forever. Pretty-printing is an option and **does not change the canonical
form** — two forms would mean two things to test.

*The escape set is minimal and stated*, because every one of the common
divergences (escaping `/`, `\u`-escaping non-ASCII) makes a byte-level round
trip fail for no reason. Numbers use the prelude's shortest-round-trip Dragon4
(D-193) rather than a second implementation.

### PA-062 — the round-trip property is a fixed point after one normalisation
**2026-09-03.** `parse(print(parse(b))) ≡ parse(b)`, and
`print(parse(print(d))) ≡ print(d)` byte for byte.

*Not* `print(parse(b)) == b`: the input may have had whitespace, a different
escape spelling or a non-canonical number, and a writer reproducing them would
be a formatter. One normalisation, then stability, is the honest property.

*Testing only tree equality would miss* a writer whose output parses to the same
tree but differs in bytes each time — a determinism failure — which is why the
second print is compared byte for byte.

---

## Plugins

### PA-070 — a plugin is a `Format` trait implementation; there is no registry
**2026-09-03.** No dynamic loading, no macro, no registration.

*The constraint is absolute:* there is **no `dlopen`**, because loading code at
run time means an FFI boundary and **in-process FFI does not exist** (D-149);
the link is closed-world by construction with no relaxing flag. A plugin is
therefore compiled into the program that uses it.

*And a registry is not merely inadvisable, it is unspellable:* it would need a
mutable module-level table, which **D-211 refuses**, and a `fixed` one could not
be extended by a consumer. Format dispatch is the application's `pick`, and the
library ships `builtin_open` over the four shipped formats as a convenience.

*The out-of-process form was considered:* a driver over the compiler's Bridge
genuinely could host a foreign parser in another process. It is enormous — a
wire protocol, a supervised child, a deadline per dispatch — and buys nothing
for a parser whose input and output are both already in the caller's memory.

*What extensibility means here* is what it means for `serde`: anyone can write
one and everything downstream works on it unchanged. Not: it can be dropped
into a running process.

### PA-071 — `dyn Format` is object-safe and is the runtime-choice path
**2026-09-03.** `step` takes a `Self->` receiver, returns no `Self`, mentions
no associated type and has no type parameters, so the trait satisfies the
object-safety rules (`TRAITS_REFERENCE.md` §4.2). Static dispatch through a
bound is the intended path and what every example uses; `dyn` costs an indirect
call per event and exists so that "choose the format from the file extension"
does not require a hand-written `pick` in every consumer.

### PA-072 — the plugin contract is enumerated and mechanically checked
**2026-09-03.** Eight obligations — grammar, never traps, never fails but
`EParseState`, idempotent, consumes every byte once, bounded allocation,
terminates, valid spans — checked by `plugin_conform<F: Format>` over a corpus.

**Every shipped format runs it, and so does a deliberately trivial fifth format
that lives in `tests/`.** That fifth one is the test of the claim that nothing
in `doc`, `emit` or the harness knows the shipped formats are special: the path
a third party takes is walked on every run.

*A plugin declares no `error:` of its own.* A format-specific condition is a
`FaultCode`, because adding a `failsafe` arm to every consuming program is not
a format's decision to make.

---

## Testing

### PA-080 — the round trip is the oracle
**2026-09-03.** Parse a corpus case, print it, parse the bytes back, and
compare the two documents structurally. **The single most valuable instrument
in the suite**, and it costs a writer the library wanted anyway (PA-060).

*Every corpus case that parses is a round-trip case*, so the oracle's coverage
is the corpus's coverage rather than a separate hand-written set.

### PA-081 — conformance corpora are vendored and committed with their provenance
**2026-09-03.** Under `tests/corpus/<name>/`, each with a `PROVENANCE.md`
recording the upstream repository, the commit hash and the date.

*Reasoning.* A build must never fetch (the compiler's D-078: a build that needs
a network fails where safety-critical software is built). And a corpus that
changed underneath us would silently change what "conformant" means — the number
would still be green and it would mean something else.

*JSONTestSuite's `i_` set gets recorded verdicts rather than pass/fail*, because
the implementation-defined cases are where the interesting divergences live and
a change to any of them should be a red run.

### PA-082 — the tree and the stream are differentially tested
**2026-09-03.** For every corpus case the event stream is captured directly and
also reconstructed by walking the `Document` the same case builds, and the two
must be identical.

*Reasoning.* This catches the class where the builder mishandles what the parser
reported correctly — a dropped member, a mis-parented value, an off-by-two in
the key/value alternation. Neither the corpus nor the round trip finds it
reliably, and **the round trip can hide it**, because a symmetric bug in the
builder and the writer cancels.

*TOML's expected-JSON encodings are a third oracle* and are worth naming
separately: they are the only check in the suite that does not go through our
own reader at all.

### PA-083 — the fuzzer, and its five invariants
**2026-09-03.** Random bytes and structured mutations of the corpora, asserting:
it never traps; it always terminates; it consumes every byte exactly once;
allocation stays under `NPARSE_MAX_SCALAR`; and **a parse that succeeds
round-trips**.

*Invariant one is the one that matters.* PA-012's no-trap rule is the library's
central claim and the fuzzer is the only thing that tests it at scale. The seed
corpus is the shapes designed to break it: a 5000-digit integer, `1e999999999`,
fifty thousand `[`, a 100 MB string, a `\u` escape at every boundary.

*Anything the fuzzer finds becomes a permanent case*, with the fault it produced
recorded in the marker. A fuzzer finding that is fixed and not kept is a fuzzer
finding that comes back.
