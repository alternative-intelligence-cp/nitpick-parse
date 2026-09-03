# Cycle 0.4 — The document

**`src/doc/`: the arena tree, the pool, ordered maps, the duplicate policy, the
accessors and the path language.** What a caller gets when they want a tree
rather than a stream.

## Why after a format rather than before

Because a value model designed before anything produced values is a value model
designed against imagination. JSON's corpus is what tells us whether the node
layout works, whether 56 bytes is right, and whether the sibling chain is
comfortable to walk — and it exists now.

## Decisions in

PA-030 … PA-034, PA-082. All settled, PA-030 on probe 05's verdict.

**Open questions to settle:** O-P1 (the duplicate-key default) — confirmed here
against the corpus, specifically that no JSONTestSuite `y_` case contains a
duplicate key our default would now reject.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.4.0 | **`Node` and the arena** — the layout, the pool, `doc_build` | 56 bytes asserted, a tree built from JSON |
| 0.4.1 | **Order and duplicates** — the sibling chain, the pair alternation, `DupPolicy` | insertion order preserved and asserted |
| 0.4.2 | **Lookup** — `doc_find`, `doc_index` | a 10 000-key map, both paths, measured |
| 0.4.3 | **The accessors** — the six numeric, `doc_text`, `doc_string`, `doc_eq` | every accessor total |
| 0.4.4 | **Paths** — `doc_path` and its closed syntax | the syntax exercised, a malformed path faulting with a span |
| 0.4.5 | **The differential test** — stream versus tree | every corpus case, both ways, identical |
| 0.4.6 | **Close** | `done/0.4/`, `0.5.0.md` written |

## Checklist

### 0.4.0 — `Node` and the arena
- [ ] `Node` exactly 56 bytes, POD, `#size_of` asserted; `check_no_owning_fields` covers it
- [ ] the arena of nodes with `Handle<Node>`, and a **stale handle answering `StaleHandle`** rather than reading freed memory (probe 04's shape made permanent)
- [ ] the pool: every scalar copied in exactly once, so a `Document`'s text is its own (D-6)
- [ ] `doc_build<F: Format>(p)` driving any format to `Done` — including the trivial fifth format from 0.3.3
- [ ] **`doc_build` uses an explicit stack** (PA-034), and so do the walk, the compare, the print and the drop
- [ ] on `Fault`, the partial arena is destroyed and the fault returned — **a partial document is never handed back** (D-22)
- [ ] `doc_destroy` consuming the document, and every test exiting 0 so a missed destroy is a trap (D-151)

### 0.4.1 — order and duplicates
- [ ] a `Map` node's chain alternates key and value, `len` counting **pairs** (D-5's off-by-two, asserted)
- [ ] insertion order preserved, asserted by building from a document with keys in a deliberately non-alphabetical order
- [ ] `DupPolicy` — `Error` (default), `First`, `Last`
- [ ] O-P1 confirmed: no JSONTestSuite `y_` case contains a duplicate key the default would reject; if one does, the decision is amended rather than the test skipped
- [ ] duplicate detection switching to an incremental index beyond `NPARSE_DUP_SCAN_MAX`, **invisible to the answer** (D-16)

### 0.4.2 — lookup
- [ ] `doc_find` as a linear scan of the pair chain, comparing pool bytes
- [ ] `doc_index` building an FNV-1a-ordered `Vec` with binary search — deterministic, no buckets, no load factor (D-13)
- [ ] the FNV convention matching the prelude's `Hash` derive, so a hash never varies between builds
- [ ] a 10 000-key map exercised through both paths, with the crossover measured and recorded

### 0.4.3 — the accessors
- [ ] `doc_int64`, `doc_uint64`, `doc_flt64`, `doc_int256`, `doc_num_text`, and each **total**, returning `Optional`
- [ ] `ND_BIG` keeping the literal's text, and `doc_int256` reading it — the reason PA-033 kept it (D-19)
- [ ] `doc_text` returning a borrow into the pool; `doc_string` allocating and **saying so in its name** (D-8)
- [ ] `doc_eq` structural, order-sensitive, comparing scalars by pool bytes; `Float` compared **by bit pattern** (D-20), which is the round-trip question rather than the numeric one
- [ ] Q-3 settled: `doc_int256` ships at 1.0; a `frac64` accessor only if a consumer appears

### 0.4.4 — paths
- [ ] `doc_path(d, root, "a.b[0].c")` with the closed syntax: `.key`, `[n]`, and `."quoted key"` (D-25)
- [ ] **no wildcards, no filters, no recursion, no expression language** — and the module header says why
- [ ] a malformed path faulting with a span **into the path string**, parsed by `nparse`'s own scanner (D-26)

### 0.4.5 — the differential test
- [ ] for every corpus case, the event stream captured directly **and** reconstructed by walking the document built from it, and the two identical (PA-082)
- [ ] this catches the builder-only class — a dropped member, a mis-parented value, the key/value off-by-two — that neither the corpus nor the round trip finds reliably
- [ ] noted in the record: the round trip (0.5) **can hide** this class, because a symmetric bug in the builder and the writer cancels. That is why this test exists and why it comes first.

## Gate

The differential test green over the whole JSONTestSuite `y_` corpus: the stream
and the tree agree, case for case.

## Watch for

- **Probe 05's verdict is what this cycle is built on.** If the arena element
  could own after all, PA-030 needs superseding and the pool becomes an
  optimisation — a materially simpler design that should be taken deliberately
  rather than discovered here.
- **The key/value alternation is the likeliest bug in the cycle**, and `len`
  counting pairs rather than chain entries is the likeliest form of it.
- **The drop is the subtle one.** A tree built by a depth-bounded parser and
  freed by a *recursive* drop is a stack overflow at the end of a **successful**
  parse. `check_no_recursion` covers it; the test that builds 50 000 levels and
  frees them is what proves it.
