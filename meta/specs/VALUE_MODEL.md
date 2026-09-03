# The document model

`Document` — what a caller gets when they want a tree rather than a stream. It
is the part of the library the prototype's five parsers each rewrote, and the
part where getting it wrong means everyone writes their own again.

---

## 1. The shape

```nitpick
pub struct:Document = {
    arena<Node>:nodes;      // generation-checked; destroy() consumes it
    Bytes:pool;             // every scalar's bytes, copied once
    Handle<Node>:root;
    uint32:count;
};
```

**Rule D-1 (PA-030) — the tree is an arena of POD nodes with a side string
pool.** Not a linked structure of owning values, and the reason is a language
rule rather than a preference:

> **An arena `get` returns a copy** (D-152, `MEMORY_REFERENCE.md` §4.2), and a
> copy of an owning value is *refused* (TYPE-046). A node holding a `string`
> could therefore not be read back **at all** — not "would be slow", not "would
> allocate": `doc.nodes.get(h)` would not compile.

So text lives in the pool and a node addresses it by offset and length.
`SAFETY.md` §6 states the rule; this is where it bites hardest.

**Rule D-2 — the arena is what makes a stale reference safe.** A `Handle<Node>`
carries a generation, and a handle that outlived its slot fails `get` with
`StaleHandle` (−4106) rather than reading freed memory. That is the use-after-free
class closed structurally, and it is the reason the tree is an arena rather than
a `Vec` of indices.

---

## 2. `Node`

```nitpick
pub struct:Node = {
    NodeKind:kind;      // 1
    uint8:flags;        // 1 — ND_BIG, ND_NEG, ND_ESCAPED
    uint16:_pad;        // 2
    uint32:len;         // 4 — pool byte length, or member count
    uint64:a;           // 8 — pool offset, or int64 value, or flt64 bits
    Handle<Node>:first; // 16 — first child, or the vacant handle
    Handle<Node>:next;  // 16 — next sibling, or the vacant handle
    Span:span;          // 8
};                      // 56 bytes

pub enum:NodeKind = { Null; Bool; Int; Float; Str; Seq; Map; Date; Time; DateTime; };
```

**Rule D-3 — no owning field, asserted.** `#size_of<Node>()` is checked by a
test, and `check_no_owning_fields` (`TESTING.md` §3) covers `Node`, `Event` and
every value stored in a `Vec` or an arena.

**Rule D-4 — children are a sibling chain, not a `Vec` per node.** A `Vec` per
node would be an owning field (D-3 refuses it) *and* a separate allocation per
container. The chain is `first` plus `next`, and a container's `len` is its
member count so a caller can size a loop without walking.

**Rule D-5 — a map's children alternate key and value.** A `Map` node's chain
is `key₀ value₀ key₁ value₁ …`, where each key is a `Str` node. This is what
preserves order (§4) with no second structure, and `len` counts **pairs**, not
chain entries — stated because it is the obvious off-by-two.

---

## 3. The pool

**Rule D-6.** Every scalar's bytes are copied into `pool` exactly once, when the
node is built. The `TextRef` lifetime rule (`EVENT_MODEL.md` §5) therefore does
not apply to a `Document`: its text is its own, and it lives as long as the
document.

**Rule D-7 — the pool is append-only within a document** and is freed with it.
There is no interning at 1.0 (§8's open item), no reference counting, and no
deduplication.

**Rule D-8 — `doc_text(d, h) -> uint8[]` is a borrow into the pool**, second
class like every borrow. A caller who needs an owned `string` calls
`doc_string(d, h)`, which allocates and says so in its name.

---

## 4. Maps preserve insertion order

**Rule D-9 (PA-031).** A `Map` node's chain is in the order the input presented
the pairs, and a writer emits them in that order.

*Reasoning.* TOML and YAML both have constructs whose meaning depends on order
(a TOML table's position relative to its parent; a YAML merge key's precedence,
were it in scope). JSON does not *require* order, but every JSON tool that
reorders keys makes every diff of every configuration file useless, which is a
cost paid by humans forever to save a hash table. Preserving order is strictly
more information, and a caller who does not care simply does not look.

*Cost accepted:* lookup is a scan (§5).

---

## 5. Lookup, and the absence of a hash map

**Rule D-10.** `doc_find(d, map, key) -> Handle<Node>?` is a **linear scan** of
the pair chain, comparing pool bytes.

**Rule D-11 — there is no hash map anywhere in the language or the prelude to
use instead.** This was measured, not assumed: `TYPE_REFERENCE.md` lists no map
type, the prelude declares none, and D-041 explicitly returned the collection
keywords to userland. So the choice is "scan" or "build one", not "scan" or
"use the standard one".

**Rule D-12 — scan is right for the size that occurs.** A configuration file's
map has ten keys and a scan beats a hash on both time and code. A map with ten
thousand keys is a different thing, and §5's answer is explicit rather than
automatic:

**Rule D-13 — `doc_index(d, map) -> MapIndex` builds a lookup index on
demand**, owned by the caller, valid until the document changes. It is an
FNV-1a-ordered `Vec<(hash, Handle)>` with binary search — deterministic, no
buckets, no load factor, and the hash is the prelude's own FNV convention
(`TRAITS_REFERENCE.md`'s `Hash` derive uses FNV-1a for the same reason: a
derived hash that varies between builds is not something a verified library can
have).

Building it is O(n log n) once; a caller doing one lookup should not, and a
caller doing thousands should. Making it explicit is what lets the caller
decide, and what keeps `Document` a plain value.

---

## 6. Duplicate keys

**Rule D-14 (PA-032).** A repeated key in one map is, by default, a
`Fault(DuplicateKey)` carrying the span of the *second* occurrence.

*Reasoning.* Duplicate-key handling is a documented source of parser
differentials: two implementations disagree about which value wins, a validator
checks one and a consumer reads the other, and the disagreement is the
vulnerability. The formats do not agree either — **TOML forbids duplicates**,
**YAML forbids them**, and **JSON leaves the behaviour undefined** (RFC 8259
§4). An error by default is the only choice that is right for two of the three
and safe for the third.

**Rule D-15 — `DupPolicy` is an option** (`EVENT_MODEL.md` §6): `Error` (the
default), `First`, or `Last`. **A format that forbids duplicates always errors
regardless of the policy** — TOML and YAML do not become permissive because a
caller asked. The option changes JSON's behaviour and nothing else, and that is
stated so nobody expects otherwise.

**Rule D-16 — detection is a scan of the pairs already in the chain**, which is
quadratic in a map's size. For a map beyond `NPARSE_DUP_SCAN_MAX` (1024 pairs)
the builder switches to an index built incrementally. The threshold is a named
constant and the switch is invisible to the answer.

---

## 7. Numbers

**Rule D-17 (PA-033) — the document stores what the format specified, and the
caller converts.**

| `NodeKind` | `a` holds | When |
|---|---|---|
| `Int` | the `int64` magnitude, `ND_NEG` in flags | the literal fitted 64 bits |
| `Int` + `ND_BIG` | a pool offset to the literal's text | it did not |
| `Float` | the `flt64` bit pattern | the format said float |

**Rule D-18 — the accessors are total and named for what they cost:**

| Accessor | Answers |
|---|---|
| `doc_int64(d, h)` | `int64?` — `NIL` if not an integer or out of range |
| `doc_uint64(d, h)` | `uint64?` |
| `doc_flt64(d, h)` | `flt64?` — exact for `Float`, nearest for a `Int` too large |
| `doc_int256(d, h)` | `int256?` — the reason `ND_BIG` keeps the text |
| `doc_num_text(d, h)` | `uint8[]` — the literal, always available |

**Rule D-19 — `ND_BIG` is not an error.** A 40-digit integer is a well-formed
JSON number and a well-formed TOML integer is not, so the *format* decides
whether to `Fault`; the *document* can always represent it, because it kept the
text. A library that had already narrowed to `int64` would have destroyed the
information before the caller could ask.

**Rule D-20 — no float is ever compared for equality by the library.** `doc_eq`
compares `Float` nodes by bit pattern, which is a different question from
numeric equality and is the one a round-trip test wants. A caller doing numeric
comparison does it themselves, knowingly.

---

## 8. Building, walking, comparing, dropping

**Rule D-21 (PA-034) — every one of these uses an explicit stack.** Building a
document from an event stream, walking it, comparing two, and freeing one are
all operations whose depth the *input* chose, and `SAFETY.md` §5 admits no
native recursion on such a path. A tree built by a depth-bounded parser and then
freed by a recursive drop is a stack overflow at the end of a successful parse,
which is the subtlest form of this bug and the one most likely to survive
review.

**Rule D-22 — `doc_build<F: Format>(p) -> Document`** drives any `Format` to
`Done` and returns the tree. On `Fault` it unwinds its stack, destroys the
partial arena, and returns the fault — a partial document is never handed back,
because a caller who forgot to check would be reading a truncated configuration
as if it were whole.

**Rule D-23 — `doc_destroy(d)` consumes the document** (a compile-time move,
like `arena.destroy()`), and an un-destroyed document is a wild-role leak the
exit-time check names (D-151). The test programs exit 0 on purpose so that a
missed destroy is a trap rather than a pass.

**Rule D-24 — `doc_eq(a, b)` is structural**, order-sensitive for sequences and
for maps, and compares scalars by their pool bytes. It is the round-trip
oracle's comparison (`WRITER_MODEL.md` §4) and therefore the most load-bearing
equality in the library.

---

## 9. Paths

**Rule D-25.** `doc_path(d, root, "a.b[0].c") -> Handle<Node>?` navigates a
document with a small, closed syntax: `.key` for a map member, `[n]` for a
sequence index, and a quoted `."key with dots"` for a key that contains a dot.
No wildcards, no filters, no recursion, no expression language.

*Reasoning.* JSONPath and JMESPath are query languages, and a query language is
a parser, an evaluator and a specification of its own — a library inside this
library. The 90% case is "reach the value at this location in a configuration
file", which the closed syntax serves in one function, and the remaining 10% is
a caller walking the tree with `doc_first`/`doc_next`, which is five lines.

**Rule D-26 — a path is parsed by `nparse`'s own scanner**, so a malformed path
is a `Fault` with a span into the path string, like everything else.

---

## 10. Open items

- ~~**the duplicate-key default**~~ — settled here as D-14; the open item lives
  in `SAFETY.md` §9 as O-P1 until cycle 0.4 confirms it against the corpora.
- **O-P8 — whether the pool should intern repeated keys.** A configuration file
  with a thousand tables repeats every key name. **Open by design:** it is a
  *measurement*, taken at cycle 0.11 against a realistic corpus, and the answer
  is either "leave it" or "intern keys only, in a side index the builder already
  has for D-16".
- **O-P9 — whether `Document` should be mutable.** At 1.0 it is built once and
  read; there is no `doc_set`. A configuration *editor* would want mutation and
  order preservation together, which is a different design (and arguably the
  CST library of `PLUGIN_MODEL.md` §7). **Recommendation:** read-only at 1.0,
  revisited when a consumer asks.
