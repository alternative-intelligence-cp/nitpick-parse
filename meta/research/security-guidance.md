# Standards bodies' security guidance for JSON, TOML, YAML and CSV, and the current TOML version — research digest

**As of 2026-10-16.** Question: What do the standards bodies currently say in each format's security considerations (RFC 8259, RFC 7493 I-JSON, TOML's current specification, YAML 1.2 and its current revision, RFC 4180), which TOML version is current, and does any of them now require what a rule in nitpick-parse permits?

## Answer

**Per-document status and security text.** Section numbers come from the fetched RFC pages. The "[mine]" notes are inferences of mine.

- **RFC 8259 (JSON).**
  - Status: Internet Standard, STD 90, December 2017. It obsoletes RFC 7159. Datatracker shows no "obsoleted by", no "updated by" and no active successor draft.
  - Security considerations (§12): the only concern is scripting languages. JSON text must not be run through `eval()`-style functions, because it "could contain executable code". There is nothing about resource exhaustion or depth. §9 allows limits on text size, nesting depth, number range and string length.
  - Errata: 16 exist, 5 of them verified.
    - 7600 (§6, technical, verified): the leading-zero ban applies to the integer part only, so leading zeros are allowed in fractions and exponents. This changes what a parser must accept.
    - 7383, 7603, 5210 and 5318 (verified): the first and third are editorial; 7603 is a technical wording fix ("Unicode characters" becomes "Unicode code points") and does not change what a parser accepts.
    - 7650 and 8438 are held for document update. 9095 is reported. 8 are rejected, including 6208 (a BOM may signal an encoding), 7673 (escape U+007F and U+0080–U+009F) and 8622 (drop "names SHOULD be unique").
  - Normative lines a parser meets: §8.1 UTF-8 MUST (for text exchanged outside closed ecosystems) and "MUST NOT add a byte order mark" (a generator rule). §4 "names within an object SHOULD be unique". §9 "A JSON parser MUST accept all texts that conform to the JSON grammar".
- **RFC 7493 (I-JSON).**
  - Status: Proposed Standard, March 2015. Datatracker shows no obsoleting or updating RFC and no active successor draft. I could not see any errata for it on the page.
  - Security considerations (§5): all RFC 7159 considerations apply, and there are "no additional security considerations specific to I-JSON". It is a profile and not a parser requirement. Its MUSTs for senders and receivers are UTF-8, no surrogates or noncharacters in strings, and no duplicate member names after unescaping. §2.2 adds a SHOULD NOT on numbers beyond IEEE 754 double range and precision.
- **ECMA-404.** 2nd edition, December 2017. The page says only that it defines syntax and not semantics. It says nothing about duplicate names or security. I could not read the standard's text itself, so ECMA-404 is not a second source for any claim here.
- **TOML.**
  - Current version: **v1.1.0**. toml.io's header shows v1.1.0 and "published 12/18/2025". The project's CHANGELOG heading is "1.1.0 / 2025-12-18". The GitHub releases page marks release 1.1.0 as Latest with the date "24 Dec" and no year. I report both dates and have not resolved them. [mine: 2025-12-18 is the spec's own date; 24 Dec is probably the GitHub release-publication date.] v1.0.0 is dated 2021-01-11.
  - Security considerations: none. The v1.1.0 text has no security section. It has a UTF-8 requirement ("must be a valid UTF-8 encoded Unicode document"), and a parser that does not reject ill-formed files may replace invalid bytes with U+FFFD.
  - Parser-relevant lines:
    - bare keys are ASCII only;
    - control characters other than tab, including U+007F, are not permitted in comments, basic strings and literal strings;
    - duplicate keys and tables are invalid;
    - "If an integer cannot be represented losslessly, an error must be thrown";
    - unlisted escapes are reserved and should error.
- **YAML.**
  - Current revision of 1.2: **1.2.2, dated 2021-10-01**. The page says "There are no normative changes from the YAML specification v1.2." yaml.org/spec/ labels `/spec/1.2/spec.html` the "final YAML 1.2".
  - Security considerations: I found none in the first 100,000 of 191,683 characters of the 1.2.2 text, or in chapters 7–10, and did not read the last ~91,000 characters. [mine: the spec appears to have no security section.]
  - Relevant normative text:
    - §3.3.1: "A YAML processor should reject ill-formed streams and unidentified aliases".
    - §3.2.1.1: mapping keys are unique.
    - §3.2.1.3 and §3.3: duplicate keys are a loading failure point.
    - Equality of a node that is its own descendant via an alias is "implementation-defined".
- **RFC 4180 (CSV).**
  - Status: Informational, October 2005. It is updated by RFC 7111 (URI fragment identifiers), which does not change the syntax. Datatracker shows no obsoleting RFC and no active successor draft.
  - Security considerations (§5, pointing to §3): CSV is passive text, but malicious binary data could exploit "buffer overruns in the program processing CSV data", and private data may be shared. The memo "does not specify an Internet standard of any kind".
  - Errata: 6 exist. 5593 and 5714 are verified and editorial. 5345 ("should" becomes "must" for quoting) and 6230 (last record must end in a line break) are technical and held for document update, so they are not in force. 7572 is held and 5464 rejected.
  - Nothing in the errata changes what a parser must accept or reject today.

**Changes from TOML v1.0.0 to v1.1.0 that change accept/reject.** The source is the project's CHANGELOG, with the release notes in agreement; both were read through a summarising fetch.

1. Inline tables may span lines and end with a trailing comma (#904). 1.0.0 rejected both.
2. `\xHH` is a new basic-string escape (#796). Under 1.0.0 it was a reserved escape and an error.
3. `\e` is a new escape (#790). Under 1.0.0 it was a reserved escape and an error.
4. Seconds are optional in date-time and time values (#894). `14:15` is now valid.
5. "Clarify that parsers are free to support any int or float size" (#1058). This may loosen the 1.0.0 integer rule. I did not fetch the 1.0.0 text, so I cannot say how.

Clarifications only, with no stated change to accept/reject:
- #950 comments never affect the tables produced
- #929 Unicode and UTF-8 references
- #859 where dotted keys define tables
- #842 newline normalisation in multi-line literal strings
- #805 sub-millisecond precision allowed

Whether #859 or #842 move any case from reject to accept is not verified. The summariser reported no entries on bare keys or control characters. The toml.io v1.1.0 page still says bare keys are ASCII only.

**Table.** The body is the standards body. "Rule" is the nitpick-parse rule or file at the given line.

| Body, words, section | Library rule (path:line) | Verdict |
|---|---|---|
| RFC 8259 §8.1: "MUST be encoded using UTF-8" | `meta/specs/FORMATS.md:31-33` (R-3); `meta/specs/SCAN_MODEL.md:94-98` (C-9) | MEETS |
| RFC 8259 §8.1: "MUST NOT add a byte order mark" (generation) | Parse side strips a BOM (`meta/specs/FORMATS.md:42`). `meta/specs/WRITER_MODEL.md` has no BOM text. | Parse: MEETS. Writer: SILENT |
| RFC 8259 §4: "names within an object SHOULD be unique" | `meta/specs/FORMATS.md:39`; `meta/specs/VALUE_MODEL.md:149-153` (D-15) | MEETS (error by default; the `First` and `Last` options relax it, which the RFC permits) |
| RFC 8259 §9: "MUST accept all texts that conform to the JSON grammar", with limits allowed | `meta/specs/FORMATS.md:40,43`; `meta/specs/SAFETY.md:253-260` | MEETS [mine: the limits are the permitted kind; a conforming 5,000-deep array or 5,000-digit number gets a Fault, which §9 allows] |
| RFC 8259 §9: "MAY accept non-JSON forms or extensions" | `meta/specs/FORMATS.md:46-49` (R-5) refuses extensions | MEETS (stricter) |
| RFC 8259 §7/§8.2: lone surrogates have "unpredictable" behaviour | `meta/specs/FORMATS.md:41`; `meta/specs/SCAN_MODEL.md:241` (C-23) | MEETS (stricter) |
| RFC 8259 §12: do not `eval()` JSON | no rule; the library only scans | SILENT (nothing to meet or break) |
| RFC 8259 erratum 7600 (verified): leading zeros allowed in fraction and exponent | `meta/specs/FORMATS.md:31` ("the whole grammar") | SILENT [mine: the JSONTestSuite gate at `meta/specs/FORMATS.md:55-59` must decide the `y_`/`n_` cases for `1.01` and `1e01`] |
| RFC 7493 §2.1: no surrogates or noncharacters in strings | `meta/specs/FORMATS.md:41` covers surrogates only; noncharacters are not mentioned | SILENT (I-JSON is not claimed) |
| RFC 7493 §2.3: "MUST NOT have members with duplicate names" | `meta/specs/FORMATS.md:39`; `meta/specs/VALUE_MODEL.md:149-153` | MEETS by default [mine: a caller who sets `DupPolicy` to `First` or `Last` leaves I-JSON, and the library never claims it] |
| RFC 7493 §2.2: numbers beyond double range "SHOULD NOT" be sent | `meta/specs/FORMATS.md:40` | SILENT (a sender rule) |
| TOML v1.1.0: "must be a valid UTF-8 encoded Unicode document" | `meta/specs/SCAN_MODEL.md:94-98` ("TOML requires it for strings and keys"); R-8 at `meta/specs/FORMATS.md:65-68` is silent | SILENT in FORMATS. [mine: C-9 says "strings and keys" only, while TOML says the whole document, including comments.] |
| TOML v1.1.0: control characters other than tab, including U+007F, not permitted in comments and strings | no rule in `meta/specs/FORMATS.md:63-95` or `meta/specs/SCAN_MODEL.md` | SILENT |
| TOML v1.1.0: bare keys are ASCII `A-Za-z0-9_-` only | `meta/specs/FORMATS.md:65` says "bare and quoted keys" only | SILENT |
| TOML v1.1.0: "Defining a key multiple times is invalid"; tables cannot be redefined | `meta/specs/FORMATS.md:81-84` (R-10); `meta/specs/VALUE_MODEL.md:150-152` | MEETS |
| TOML v1.1.0: "If an integer cannot be represented losslessly, an error must be thrown" | `meta/specs/VALUE_MODEL.md:183-187` (D-19) says `ND_BIG` is not an error in the document and that the format decides whether to `Fault`. No TOML rule states that decision. | SILENT. [mine: `ND_BIG` keeps the text and `doc_int256` reads it, so a TOML reader that does not fault on a 40-digit integer would permit what TOML forbids if its target is only 64-bit.] |
| TOML v1.1.0: unlisted escapes are reserved and should error | no rule | SILENT |
| TOML v1.1.0: seconds optional; the RFC 3339 exception | `meta/specs/FORMATS.md:70-79` (R-9) says the syntax matches TOML's grammar, which is pinned at v1.0.0 | SILENT on the difference. R-9 gives no pinned grammar that admits `14:15`. |
| YAML 1.2.2 §3.3.1: reject ill-formed streams and unidentified aliases | `meta/specs/FORMATS.md:114-118` (aliases and anchors out; `Fault(Unsupported)`) | MEETS |
| YAML 1.2.2 §3.2.1.1: keys unique | `meta/specs/VALUE_MODEL.md:144-152` (D-15 always errors for YAML). R-13 at `meta/specs/FORMATS.md:101-125` does not state it. | MEETS (the rule sits in VALUE_MODEL, not FORMATS) |
| YAML 1.2.2: "no normative changes" from 1.2; no revision is named by the library | `meta/specs/FORMATS.md:15-17` and `meta/specs/FORMATS.md:19-21` (R-1) say only "1.2 core schema" | SILENT (the revision is not stated; it can be 1.2.2) |
| RFC 4180 §3: malicious binary data and buffer overruns in the CSV processor | `meta/specs/FORMATS.md:184-186` (R-19, bytes unvalidated); `meta/specs/SAFETY.md:130,185,203` (S-8, S-13, S-14) | MEETS [mine: every byte is bounds-checked and arithmetic cannot trap] |
| RFC 4180 §2: "should contain the same number of fields" | `meta/specs/FORMATS.md:193-195` (R-21) | MEETS |
| RFC 4180 §2: "Spaces are considered part of a field and should not be ignored" | `meta/specs/FORMATS.md:176` (`trim_fields`, default false) | MEETS |
| RFC 4180 §2: line break is CRLF | `meta/specs/FORMATS.md:179` (`LineEnd` default `Any`) | MEETS [mine: RFC 4180 is Informational, so accepting LF and CRLF is not forbidden] |

## Evidence

- https://www.rfc-editor.org/rfc/rfc8259.txt — retrieved 2026-10-16 — "The names within an object SHOULD be unique." (§4); "JSON text exchanged between systems that are not part of a closed ecosystem MUST be encoded using UTF-8" (§8.1); "Implementations MUST NOT add a byte order mark (U+FEFF) to the beginning of a networked-transmitted JSON text." (§8.1); "Obsoletes: 7159"
- https://www.rfc-editor.org/rfc/rfc8259.html — retrieved 2026-10-16 — "A JSON parser MUST accept all texts that conform to the JSON grammar." (§9); "This generally constitutes an unacceptable security risk, since the text could contain executable code" (§12)
- https://datatracker.ietf.org/doc/rfc8259/ — retrieved 2026-10-16 — "RFC - Internet Standard (December 2017)"; STD 90; no obsoleted-by, updated-by or successor draft shown
- https://errata.rfc-editor.org/search/?rfc_number=8259 — retrieved 2026-10-16 — 16 errata; verified: 7383, 7600 ("Limit the leading-zero ban to the integer part"), 7603, 5210, 5318; rejected includes 6208, 7673, 8622
- https://www.rfc-editor.org/rfc/rfc7493.txt — retrieved 2026-10-16 — "Objects in I-JSON messages MUST NOT have members with duplicate names." (§2.3); "There are no additional security considerations specific to I-JSON." (§5)
- https://datatracker.ietf.org/doc/rfc7493/ — retrieved 2026-10-16 — "Proposed Standard (March 2015)"; no obsoleted-by, updated-by or successor draft shown
- https://ecma-international.org/publications-and-standards/standards/ecma-404/ — retrieved 2026-10-16 — "ECMA-404, 2nd edition, December 2017" (the page lists it with the 1st edition, October 2013, archived)
- https://github.com/toml-lang/toml/releases — retrieved 2026-10-16 — "Release 1.1.0 ... Latest"; "Allow newlines and trailing commas in inline tables (#904)."; "Add `\xHH` notation to basic strings for codepoints <255 (#796)"; "Add `\e` escape for the escape character (#790)"; "Seconds in datetime and time values are now optional (#894)."; "Clarify that parsers are free to support any int or float size (#1058)."
- https://raw.githubusercontent.com/toml-lang/toml/main/CHANGELOG.md — retrieved 2026-10-16 — heading "1.1.0 / 2025-12-18"; v1.0.0 dated 2021-01-11 (same bullets as the releases page)
- https://github.com/toml-lang/toml/blob/main/CHANGELOG.md — retrieved 2026-10-16 — same 1.1.0 list; "a flat list" with no further entries on bare keys, control characters or DEL
- https://toml.io/en/ — retrieved 2026-10-16 — page header v1.1.0, "Read the full spec" links to `latest`; v1.0.0 listed at `/en/v1.0.0`
- https://toml.io/en/v1.1.0 — retrieved 2026-10-16 — "TOML v1.1.0 (published 12/18/2025)"; "A TOML file must be a valid UTF-8 encoded Unicode document."; "Bare keys may only contain ASCII letters, ASCII digits, underscores, and dashes (A-Za-z0-9_-)."; "If an integer cannot be represented losslessly, an error must be thrown."; "Control characters other than tab (U+0000 to U+0008, U+000A to U+001F, U+007F) are not permitted in comments."
- https://raw.githubusercontent.com/toml-lang/toml/1.1.0/toml.md — retrieved 2026-10-16 — same quotes, plus "Defining a key multiple times is invalid." and "All other escape sequences not listed above are reserved; if they are used, TOML should produce an error."; "seconds may be omitted, in which case `:00` will be assumed"; no security text
- https://yaml.org/spec/ — retrieved 2026-10-16 — "YAML 1.2 (latest patched specification, labeled "final YAML 1.2")" at /spec/1.2/spec.html; the page gives no 1.2.x number
- https://yaml.org/spec/1.2.2/ — retrieved 2026-10-16 — "Revision 1.2.2 (2021-10-01)"; "There are no normative changes from the YAML specification v1.2."; "A YAML processor should reject ill-formed streams and unidentified aliases."; "A mapping's keys are unique if no two keys are equal to each other."; no security section in the 100,000 characters read at offset 0 or in chapters 7–10 at offset 100,000
- https://www.rfc-editor.org/rfc/rfc4180.txt — retrieved 2026-10-16 — "This memo provides information for the Internet community. It does not specify an Internet standard of any kind."; "buffer overruns in the program processing CSV data" (§3); "See discussion above in section 3." (§5); "Each line should contain the same number of fields throughout the file."; "Spaces are considered part of a field and should not be ignored."
- https://datatracker.ietf.org/doc/rfc4180/ — retrieved 2026-10-16 — "Informational (October 2005)"; updated by RFC 7111; no obsoleted-by or successor draft shown
- https://errata.rfc-editor.org/search/?rfc_number=4180 — retrieved 2026-10-16 — 6 errata: 5593 and 5714 verified editorial; 5345 and 6230 held for document update; 7572 held; 5464 rejected

## What would change this

The request's condition is "a body now requires what a rule here permits". Result: **no clear case that came true, but one TOML item is open**. Item by item:

- **JSON (RFC 8259, RFC 7493, ECMA-404).** Not true.
  - Every RFC 8259 MUST is met by R-3 and R-4 (`meta/specs/FORMATS.md:31-44`). The BOM rule is a generator rule, and the writer is silent (`meta/specs/WRITER_MODEL.md`).
  - RFC 7493's MUSTs bind I-JSON senders and receivers. `meta/specs/FORMATS.md:14` claims RFC 8259, not I-JSON.
  - Erratum 7600 is the only verified erratum that changes acceptance. The rule that decides it is the JSONTestSuite gate (`meta/specs/FORMATS.md:55-59`, R-7).
- **TOML.** Two parts.
  - Version. Current is v1.1.0, and the library pins v1.0.0 (`meta/specs/FORMATS.md:15`, R-1 at 19-21; currency row at `meta/roadmap/0.0/0.0.1_tools/step5.patch:75`). The five changes above make v1.1.0 accept documents that v1.0.0 rejects. Nothing in TOML v1.1.0 requires a parser to accept them, so pinning v1.0.0 breaks no requirement. The rule that decides is R-1 (PA-054, confirmed present as heading `### PA-054`, which says the pinned version is recorded). The choice of version is the cycle-0.0 plan's PD-137, as the step5 patch states. This digest does not make it.
  - Requirements. TOML's "error must be thrown" for an integer that cannot be represented losslessly is not stated in any FORMATS rule. D-19 (`meta/specs/VALUE_MODEL.md:183-187`) leaves it to "the format", and R-8 is silent. That is the one open case, and it needs a TOML rule and a toml-test case. The UTF-8 scope (document versus strings and keys), control characters, ASCII bare keys and reserved escapes are also SILENT. None of these is a case of the library permitting what the standard forbids, since nothing is stated.
- **YAML.** Not true. YAML 1.2.2 has no security section, and R-13 refuses aliases, anchors, tags, directives and multiple documents, which is stricter than the spec. Duplicate keys always error (D-15). The revision of 1.2 is still not named by the library. The deciding rule is R-1 (`meta/specs/FORMATS.md:19-21`) plus the gate at `meta/specs/FORMATS.md:138-143`. That sentence is unchanged and should read "1.2.2 (2021-10-01)" when stated.
- **CSV (RFC 4180).** Not true. It is Informational, and its only requirements are "should". Stricter library defaults (R-21 and `trim_fields` false) meet them. The held errata 5345 and 6230 are not in force. If they were applied, the line-break and quoting rules (`meta/specs/FORMATS.md:176-179`) would be the ones to re-check.
- **Active successor drafts.** None was shown for RFC 8259, RFC 7493 or RFC 4180. A later datatracker check could differ, since datatracker showed the pages as last updated 2026-05-20.

## Confidence and gaps

**Medium-high.**

- Two independent primaries agree on: the TOML v1.1.0 text (toml.io and the tagged toml.md), the 1.1.0 changelog list (releases page and CHANGELOG), RFC 8259 status and errata (datatracker and the errata page), and RFC 4180 status (the RFC and datatracker).
- Single-source claims: the RFC 7493 text and the YAML 1.2.2 revision both rest on one primary page each (the YAML spec and its index state the same revision date). ECMA-404 gave only a catalogue page, so no second source on JSON semantics. The "1.2" label on yaml.org/spec/ gives no 1.2.x number.
- Fetch limits: all pages were read through a summarising fetch with a 125-character quote cap, so some quotes are fragments. The last ~91,000 characters of the YAML 1.2.2 spec were not read, so "no security section" is not fully proved. The v1.0.0 spec text was not fetched, so the integer-size change (#1058) and the changelog's completeness are inferred from the changelog only.
- Unresolved: the TOML v1.1.0 date (2025-12-18 on the spec and CHANGELOG, "24 Dec" with no year on the GitHub releases page). RFC 7493 errata count was not seen.
- Budget: 23 of 24 fetches used. Stale after 90 days, on 2027-01-14.
