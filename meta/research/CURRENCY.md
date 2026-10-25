# Currency — the facts from outside the compiler tree this plan rests on

One row per standard, data release, corpus, reference implementation and outside tool the plan
names, with the version pinned, the day it was checked, the primary source, and the decision that
pins it (the workbench research skill's §7). **A row unchecked for six months is stale, and a
cycle whose rows are unchecked is not ready to start.** Facts about the language are never rows
here: they are read in the compiler's tree at the pinned commit. Created by cycle 0.0.1
(PA-112); a format's rows are CHECKED by the cycle that first depends on it, and the table
says which.

| Depends on | Pinned | Checked | Source | Decision |
|---|---|---|---|---|
| GitHub Actions' runner image — CI's `runs-on` | `ubuntu-24.04` | by cycle 0.0.1's first CI run, whose log the record quotes | github.com/actions/runner-images | PA-111 |
| GitHub's `actions/checkout` and `actions/cache` | `@v4` each, as `nitpick-regex`'s and `nitpick-time`'s workflows | by the same run; the early ecosystem audit's EK2 recorded their Node 20 runtime as deprecated, and the run's log says whether GitHub still warns | github.com/actions/checkout, github.com/actions/cache | PA-111 |
| LLVM's release asset — what CI installs | `LLVM-20.1.8-Linux-X64.tar.xz` at `llvmorg-20.1.8` (the version is the compiler's D-349, read in its tree), and since cycle 0.0.1a by content: sha256 `1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6`, 2 021 269 412 B, which CI's install step checks before it unpacks | 2026-10-23, at cycle 0.0.1a's planning: [the asset streamed whole, GitHub's record of it and the project's provenance](llvm-release-asset.md); and by cycle 0.0.1a's first CI run, the second reading, whose log its record quotes | github.com/llvm/llvm-project/releases | PA-111 |
| Python — the harness's interpreter | 3.12.3, the version on the workbench and on `ubuntu-24.04` | by cycle 0.0.2, which writes the harness | python.org | PA-112 |
| UTF-8 — what a JSON, TOML or YAML input must be (`SCAN_MODEL.md` §3) | RFC 3629 (STD 63) and the Unicode Standard's Table 3-7, the edition to be named | **not yet** — cycle 0.1, whose decoder reads it, checks it before it starts | rfc-editor.org/rfc/rfc3629; unicode.org | PA-013 |
| JSON | RFC 8259 | not yet — cycle 0.3 | rfc-editor.org/rfc/rfc8259 | PA-050 |
| TOML | v1.0.0, as `FORMATS.md` names it. **v1.1.0 is published** (the workbench's currency audit of 2026-10-09, which the second research item below read at the source before cycle 0.0's first probe), and that item's digest lists the five changes the project's changelog gives from v1.0.0 to v1.1.0 in what a parser accepts, the fifth, on integer and float sizes, one that may loosen the integer rule ([`security-guidance.md`](security-guidance.md)) | not yet — cycle 0.6.0 decides the version (PA-054 as PA-112 amends it) | toml.io; github.com/toml-lang/toml/releases | PA-054 |
| CSV | RFC 4180, and the dialects `FORMATS.md` §6 names | not yet — cycle 0.7 | rfc-editor.org/rfc/rfc4180 | PA-050 |
| YAML | 1.2's core schema; which revision of 1.2 is not yet stated — the current one is 1.2.2, of 2021-10-01, "no normative changes from the YAML specification v1.2" ([`security-guidance.md`](security-guidance.md)) | not yet — cycle 0.8, which names the revision (R-1) | yaml.org/spec | PA-051 |
| RFC 3339 — the shape of TOML's date-times | RFC 3339 | not yet — cycle 0.6 | rfc-editor.org/rfc/rfc3339 | PA-054 |
| IEEE 754 binary64 — what `num_flt64` rounds to | IEEE 754-2019 | not yet — cycle 0.4 | ieee.org | PA-033 |
| The corpora: JSONTestSuite, toml-test, the yaml-test-suite, the W3C CSVW tests | a commit each, recorded in each corpus's `PROVENANCE.md` — toml-test's with the TOML version its gate runs, chosen by `-toml=<version>` or that version's `tests/files-toml-<version>` list and never by the runner's default, which its v2.0.0 notes and its README state differently; the yaml-test-suite's from a dated `data-<date>` tag, never its force-pushed `data` branch ([`security-vectors.md`](security-vectors.md)) | not yet — each with its format's cycle | each project's repository | PA-053, PA-081 |
| Research item 1 below — known defects in the prior art and the reference implementations | what its digest records, as of its date | by cycle 0.0's first work dispatch, before any probe: [`security-defects.md`](security-defects.md), stale ninety days after its date | cve.org, nvd.nist.gov, each project's tracker | PA-112 |
| Research item 2 below — the standards bodies' current guidance, and the current TOML version | what its digest records, as of its date | by the same dispatch: [`security-guidance.md`](security-guidance.md), stale ninety days after its date | rfc-editor.org, toml.io, yaml.org | PA-112 |
| Research item 3 below — the current versions of the test vectors | what its digest records, as of its date | by the same dispatch: [`security-vectors.md`](security-vectors.md), stale ninety days after its date | each corpus's repository | PA-112 |

## The research this library owes, because it is security-sensitive

**`nparse` is security-sensitive** (PA-112): its input is, by design, bytes somebody else
controls (`README.md`'s "What makes it different"), and three of its decisions exist only because
an input can be hostile — PA-008 (no input reaches an error identity), PA-012 (no arithmetic on
input traps) and PA-022 (no input-controlled recursion). So the workbench research skill's §8
applies, and these three requests are owed, each in its §3 shape, each `sensitivity: security`
(two independent primaries, stale after ninety days), each filed here as a digest, as its row cites it:

1. **Known defects in the prior art and the reference implementations** the formats' cycles will
   read — parsers of JSON, TOML, YAML and CSV: their published vulnerabilities and the classes they
   fall in (nesting depth, numeric overflow, duplicate keys, alias expansion, quadratic scans,
   invalid UTF-8 accepted). *Would change the plan if* a class is one no rule here guards.
2. **The standards bodies' current guidance** for each format's security considerations — RFC
   8259's, RFC 7493 (I-JSON)'s, TOML's current specification's, YAML 1.2's, RFC 4180's — and
   which TOML version is current. *Would change the plan if* a body now requires what a rule here
   permits.
3. **The current versions of the test vectors** — JSONTestSuite, toml-test (and which TOML version
   its sets encode), the yaml-test-suite, the CSVW tests. *Would change the plan if* a corpus's
   current version judges a case differently from the version a cycle planned against.

**They gate cycle 0.0's work** (PA-112): its first work dispatch, cycle 0.0.0's, carries their
three digests, and its worker files them here before any probe runs, so that a finding that asks the
language a question becomes a cycle-0.0 probe before it is anything else (the workbench plan skill);
the section below says where every other finding is held, and who decides it. The orchestrator
dispatches the requests: by the workbench's rule on research, more than one fetch is a request to the
researcher, who never writes into a repository. A later cycle reads the three dates before it starts,
since each is stale ninety days after its own, and all three are re-run at hardening.

### What the three found, and where each finding is held

The three are each `As of` 2026-10-16, and their gate fired that day, at cycle 0.0's planning: the
first's and the third's *would change the plan if* came true, and the second contradicted this table's
TOML row as the plan had written it, which said nobody had compared v1.0.0 and v1.1.0. So the plan was
re-cut that day, before any probe ran, to hold each finding where the cycle that owns it will read it.
None asks the language a question, by the libraries' reviewer's reading, so none became a probe. Each
digest states its own confidence and gaps, among them claims that rest on one primary source where a
`security` request asks for two.

- **[`security-defects.md`](security-defects.md)** — eleven defect classes with published records, by its own
  count: its table marks one of the eleven "Not a separate record class". Two have no full guard here:
  - CSV formula injection, a field that begins `=`, `+`, `-` or `@`, with no rule at all (`WRITER_MODEL.md`
    W-9 sets only JSON's escapes): the [0.7 roadmap](../roadmap/0.7/README.md), at 0.7.4;
  - the quadratic class, guarded in part: `VALUE_MODEL.md` D-16's index past 1024 pairs, if it takes D-13's
    unkeyed FNV-1a order — the [0.4 roadmap](../roadmap/0.4/README.md), at 0.4.1; TOML's header and
    dotted-key resolution, whose cost no rule bounds (`FORMATS.md` R-11) — the
    [0.6 roadmap](../roadmap/0.6/README.md), at 0.6.2; and the line and column count a rendered fault
    needs, already O-P3, a measurement taken at cycle 0.9.

  And its partial points:
  - D-16's bound, 1024 pairs, which no limits row names yet: the 0.4 roadmap's switch, at 0.4.1, names it;
  - YAML's alias expansion, guarded only by R-13's refusal while the budget R-14 promises is unwritten: the
    [0.8 roadmap](../roadmap/0.8/README.md), at 0.8.0;
  - `SAFETY.md` §7's `NPARSE_MAX_SCALAR` row, "a single JSON string", which leaves its reach to a TOML
    string, a CSV field and a YAML scalar unstated: cycle 0.0.4, whose `limits.npk` quotes the row and whose
    plan hands the reach on to cycles 0.6, 0.7 and 0.8. No row names a total for a document's nodes or its
    pool's bytes either (its item 4), and S-19's bound for a `Document`, "by the node and pool growth its
    arena does", states no function of the input: the [0.4 roadmap](../roadmap/0.4/README.md) holds it at
    0.4.0, which states nodes and pool bytes against the input's length and decides whether a per-parse
    total joins `SAFETY.md` §7's table, and each later format's cycle re-reads it;
  - an input over 4 GiB, which `SCAN_MODEL.md` C-5 refuses with `EParseState` while `SAFETY.md` §3 says no
    byte stream reaches either identity: the workbench's question 36, answered by the author on 2026-10-16,
    (A) — an ordinary `Fault` of its own kind — which cycle 0.1's decision records, at 0.1.1 of [its roadmap](../roadmap/0.1/README.md).
- **[`security-guidance.md`](security-guidance.md)** — no standards body clearly requires now what a rule
  here permits; its one open case is TOML's lossless-integer rule, which no rule here states. It
  contradicted the TOML row by listing what v1.1.0 changes:
  - the version, which stays cycle 0.6.0's to decide: the TOML row above, and the 0.6 roadmap's version
    item, at 0.6.0;
  - what TOML's text requires and no rule here states — the whole document UTF-8, no control character but
    tab in a comment or a string, ASCII bare keys, an unlisted escape an error, and an error for an integer
    that cannot be represented losslessly, which `VALUE_MODEL.md` D-19 leaves to the format: the 0.6
    roadmap, at 0.6.0 and 0.6.1; and `SCAN_MODEL.md` C-9's "strings and keys" for TOML: the 0.1 roadmap,
    at 0.1.3;
  - YAML 1.2's current revision, 1.2.2: the YAML row above;
  - RFC 8259's verified erratum 7600, which limits the leading-zero ban to a number's integer part: no
    line — R-7's JSONTestSuite gate decides those cases, in cycle 0.3.
- **[`security-vectors.md`](security-vectors.md)** — toml-test carries TOML 1.0 and 1.1, its sources
  disagree on its default, and on 2026-09-15 it withdrew its two leading-BOM valid cases: the corpora row
  above, and the 0.6 roadmap's corpus, at 0.6.0. The yaml-test-suite is vendored from a dated tag: the
  corpora row. JSONTestSuite and the CSVW tests show no change it found: no line, and their cycles, 0.3
  and 0.7, check their rows before they start.
