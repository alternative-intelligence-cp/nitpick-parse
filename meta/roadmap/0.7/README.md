# Cycle 0.7 — CSV

**`src/format/csv.npk` and `src/emit/csv.npk`: RFC 4180 plus the dialects that
occur in practice.** The simplest grammar in the set and the weakest
specification, which makes it the one where the *corpus* has to do the work the
specification does not.

## Why it is not trivial

The grammar is two pages. The difficulty is that **CSV has no authority**: every
tool that writes it does something slightly different, and a library that
implements only RFC 4180 will reject most real files. So the cycle is mostly
about drawing the dialect surface deliberately — which departures are options,
which are refused, and why — rather than about parsing.

## Decisions in

PA-050, PA-053, PA-060. All settled.

**Open questions to settle:** none.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.7.0 | **The dialect surface** — the struct, the defaults, the incoherence checks | `dialect_rfc4180()` and the refusals |
| 0.7.1 | **The reader** — records, quoting, embedded separators and newlines | every quoting edge |
| 0.7.2 | **Headers and ragged rows** — the map shape, `allow_ragged` | a shifted column caught rather than absorbed |
| 0.7.3 | **The corpus** — hand-built plus the W3C CSVW cases | the weakest gate, made as strong as it can be |
| 0.7.4 | **The writer** — the canonical form, the quoting rule | the round trip green |
| 0.7.5 | **Close** | `done/0.7/`, `0.8.0.md` written |

## Checklist

### 0.7.0 — the dialect surface
- [ ] `Dialect` with the eight fields from `specs/FORMATS.md` §6 and `dialect_rfc4180()`
- [ ] **incoherent dialects are `EParseState` at construction** (E-21): delimiter equal to quote, delimiter equal to the escape, a delimiter that is `\r` or `\n`
- [ ] the defaults documented field by field, each with the practice it accommodates

### 0.7.1 — the reader
- [ ] records as sequences of `Raw` scalars
- [ ] **CSV does not validate UTF-8** (PA-013, R-19) — a Latin-1 spreadsheet export parses, and there is a test with one
- [ ] quoting: doubled quotes, embedded delimiters, embedded newlines, a quote mid-field, an unterminated quote
- [ ] `LineEnd.Any` handling `\n`, `\r\n` and a mixed file
- [ ] an empty file, a header-only file, a trailing newline and its absence, a BOM
- [ ] a 100 MB file parsed with **allocation constant in the input size**, measured

### 0.7.2 — headers and ragged rows
- [ ] `has_header` producing a sequence of **maps** keyed by the header row (R-20) — not a third container shape
- [ ] `allow_ragged` defaulting to **false**, and a short or long row being `Fault(BadRow)` (R-21) — because a silently short row is how a column shifts and nobody notices until the numbers are wrong
- [ ] a duplicate header name handled by `DupPolicy`, like any other map

### 0.7.3 — the corpus
- [ ] the W3C CSVW test cases vendored with `PROVENANCE.md`
- [ ] **a hand-built corpus, deliberately larger than the others**, because CSV's gate is the weakest of the four and `specs/FORMATS.md` R-22 says so rather than hiding it: every dialect combination, every quoting edge, embedded newlines and delimiters, a BOM, CRLF and LF and mixed, an empty file, a header-only file, and the 100 MB file
- [ ] the pass count exact

### 0.7.4 — the writer
- [ ] the canonical form: the dialect's delimiter and line ending, a field quoted **iff** it contains the delimiter, the quote, `\r` or `\n`, no trailing delimiter
- [ ] `EParseEncode` for what CSV cannot represent: a nested container, a map value that is not a scalar
- [ ] the round trip green over the corpus, per dialect

## Gate

The round trip green over every dialect combination in the hand-built corpus,
and the 100 MB file parsed in constant memory.

## Watch for

- **The corpus is the deliverable here, more than the parser.** CSV's
  specification will not catch a defect; only cases will. Time spent enlarging
  the corpus is better spent than time spent reading RFC 4180 again.
- **Do not be tempted to sniff the dialect.** Auto-detecting the delimiter is a
  heuristic, heuristics vary with input, and a library whose behaviour varies
  with input is one whose output nobody can predict. A caller who needs sniffing
  writes it — it is twenty lines and it is *their* heuristic.
