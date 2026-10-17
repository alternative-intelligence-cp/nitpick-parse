# Current versions of the JSON, TOML, YAML and CSV test corpora — research digest

**As of 2026-10-16.** Question: What are the current versions of the test corpora nitpick-parse gates on (JSONTestSuite; toml-test, and which TOML version its sets encode; the yaml-test-suite; the W3C CSVW tests), and does any corpus's current version judge a case differently from the version the library's cycles planned against?

## Answer
One corpus, toml-test, has moved in a way that matters to the plan. It has a tagged release, v2.2.0 (2026-04-30), and its latest commit is `ff49d10` (2026-09-15). It encodes both TOML v1.0 and v1.1, and TOML v1.1.0 was released 2025-12-18. The library assumes v1.0.0 (`meta/specs/FORMATS.md:15`, `meta/specs/FORMATS.md:63`).

Whether a consumer must choose a version explicitly is unresolved, because toml-test's two primary sources disagree. The v2.0.0 release notes say 1.1 became the default. The current README example is annotated "Default of TOML 1.0".

Two further changes are verified.
- toml-test's `tests/files-toml-1.0.0` and `tests/files-toml-1.1.0` manifests are the version selectors.
- On 2026-09-15 the project deleted two valid cases, `utf8-bom-01` and `utf8-bom-02`, from both manifests.

| Corpus | Current version | Spec version encoded; how selected | Verdict changed vs the library's assumption | Moves a gate? |
|---|---|---|---|---|
| JSONTestSuite (R-7) | No tags or releases. Latest commit `1ef36fa01286573e846ac449e8683f8833c5b26a`, 2024-11-22, "Fix typos". | The README gives no RFC or version. It defines only the prefixes `y_` (must accept), `n_` (must reject) and `i_` (may accept or reject). No selector. | None found. The last commit is typo-only and 2 years old. I did not diff cases. | No. |
| toml-test (R-12) | Tag v2.2.0, 2026-04-30. Default branch `main`, latest commit `ff49d109861c1ad25af53f687f2aef19ab650600`, 2026-09-15, "Add CONTRIBUTING.md". | TOML v1.0 and v1.1. Select with `toml-test copy -toml=1.1` (and `-toml=1.0`, `-toml=latest`). The `tests/files-toml-1.0.0` and `tests/files-toml-1.1.0` lists name the files for each version. | Yes, in two ways. (a) 1.1 relaxes 1.0: multi-line inline tables with trailing commas, `\xHH`, `\e`, and optional seconds in times are newly valid. (b) The BOM valid cases were removed (see Evidence). | Yes, if the vendored copy is the 1.0.0 file list or the 1.0.0 selection: only the BOM removal applies. With 1.1 files or `latest`, R-12 would wrongly reject those inputs. This is my inference. |
| yaml-test-suite (R-16, V-11) | Newest dated tag `v2022-01-17` (the corresponding `data-2022-01-17` tag is the data release). Default-branch commit `da267a5c4782e7361e82889e76c0dc7df0e1e870`, 2025-12-25, a README "using libraries" merge. No GitHub Releases. | The README names no YAML version. Selection is by dated data tag. | None found. The newest data tag is 2022-01-17 and later default-branch commits touch the README only (the two I saw). | No, with one gap noted below. |
| W3C CSVW tests (R-22) | No tags. `gh-pages` latest commit `b3f461db0e86a68c019bc1f912e86f3555907e34`, 2026-05-22, "Update README.md". The only release link is `final-release-WG-2016`. | CSV on the Web, with JSON, RDF, Validation and Non-normative test sets. The page counts are 270, 270, 282 and 18. It encodes no RFC 4180 variants and has no selector. | None found. The repository-level latest commit is a README edit, not a case change. | No. |

## Evidence
- https://github.com/nst/JSONTestSuite — retrieved 2026-10-16 — "y_: the parser must accept the content. n_: the parser must reject the content. i_: the parser may accept or reject the content." (paraphrased by the fetch tool). The page shows no Releases entries and 200 commits.
- https://api.github.com/repos/nst/JSONTestSuite/commits?per_page=1 — retrieved 2026-10-16 — sha 1ef36fa01286573e846ac449e8683f8833c5b26a, author date 2024-11-22T12:55:41Z, "Merge pull request #139 from hsjoihs/patch-hsjoihs", body "Fix typos"
- https://api.github.com/repos/nst/JSONTestSuite/tags — retrieved 2026-10-16 — the tag list is empty.
- https://github.com/toml-lang/toml-test — retrieved 2026-10-16 — "Compatible with TOML versions v1.0 and v1.1."
- https://raw.githubusercontent.com/toml-lang/toml-test/main/README.md — retrieved 2026-10-16 — "# Default of TOML 1.0", "# Use TOML 1.1", "% toml-test copy -toml=1.1 ./tests", and "tests/files-toml-1.0.0 and tests/files-toml-1.1.0 ... contain a list of files that should be run for that TOML version."
- https://api.github.com/repos/toml-lang/toml-test/releases?per_page=3 — retrieved 2026-10-16 — v2.2.0 published 2026-04-30T16:19:17Z, "several minor bug fixes to the test runner and one additional test". v2.1.0 published 2025-12-27 restores the `list` command and the `tests/files-toml-*` files. v2.0.0 published 2025-12-18 is a breaking release "that makes TOML 1.1 the default version to test"; "Testing 1.0 now requires -toml=1.0." The two sources conflict on the default. The fetch tool summarised these; it did not quote them verbatim.
- https://api.github.com/repos/toml-lang/toml-test/commits?per_page=3 — retrieved 2026-10-16 — ff49d109861c1ad25af53f687f2aef19ab650600, 2026-09-15T19:50:05Z, "Add CONTRIBUTING.md". Next is 0d1c92ecd83a36e970929b09088d49e4d2bf92b1, 2026-09-15, "Back out UTF-8 BOM tests".
- https://api.github.com/repos/toml-lang/toml-test/commits/0d1c92ecd83a36e970929b09088d49e4d2bf92b1 — retrieved 2026-10-16 — the commit removes `tests/valid/utf8-bom-01.toml` and `tests/valid/utf8-bom-02.toml` from both file lists, and adds a README note that "the spec does not say whether a document may start with a UTF-8 BOM, so implementations may allow or forbid it" (fetch-tool paraphrase). Tests for a BOM not at the start of a document stay.
- https://raw.githubusercontent.com/toml-lang/toml/main/CHANGELOG.md — retrieved 2026-10-16 — "TOML v1.1.0, released 2025-12-18": inline tables may span lines and end with a trailing comma ("Previously an inline table had to be on a single line and couldn't end with a trailing comma."); `\xHH` escape; `\e` escape; optional seconds in datetime and time values. This is the standards-body-side source on what 1.1 changed.
- https://toml.io/en/ — retrieved 2026-10-16 — the page header shows "v1.1.0" as the latest version. No date on the page.
- https://github.com/yaml/yaml-test-suite — retrieved 2026-10-16 — "The releases are made from the `data` branch", with a warning not to use that branch directly because it is "squashed and force pushed from time to time", and a direction to clone a dated `data-YYYY-MM-DD` tag. No version of YAML is named.
- https://api.github.com/repos/yaml/yaml-test-suite/git/matching-refs/tags/data — retrieved 2026-10-16 — newest data tag is `data-2022-01-17` (tag object 5f49729577242103ae23838ac2ad4d9145aec126); earlier ones are 2021-10-09, 2020-08-01, 2020-02-11, 2019-09-17 and 2018-01-02.
- https://api.github.com/repos/yaml/yaml-test-suite/tags?per_page=5 — retrieved 2026-10-16 — `v2022-01-17` 45db50aecf9b1520f8258938c88f396e96f30831, then v2021-10-09, v2020-08-01, v2020-02-11 and v2019-09-17.
- https://api.github.com/repos/yaml/yaml-test-suite/releases?per_page=3 — retrieved 2026-10-16 — an empty list.
- https://api.github.com/repos/yaml/yaml-test-suite/commits?per_page=2 — retrieved 2026-10-16 — da267a5c4782e7361e82889e76c0dc7df0e1e870, 2025-12-25T21:01:26Z, "Merge pull request #154 from maxbeckers/patch-2"; the previous one is ebfd6cdaf257f7033ee9a1dd53432281a5580d67, 2025-11-26.
- https://github.com/w3c/csvw — retrieved 2026-10-16 — the page lists 2,458 commits on `gh-pages`, tests in `tests/`, and a single release link, `final-release-WG-2016`.
- https://api.github.com/repos/w3c/csvw/commits?per_page=1 — retrieved 2026-10-16 — b3f461db0e86a68c019bc1f912e86f3555907e34, 2026-05-22T16:45:30Z, "Update README.md"
- https://w3c.github.io/csvw/tests/ — retrieved 2026-10-16 — "CSVW Test Cases"; it lists JSON (270), RDF (270), Validation (282) and Non-normative (18) entries. The fetch tool read only the first 100,000 of about 330,000 characters.

Repository files checked:
- `meta/specs/FORMATS.md:15` (TOML v1.0.0), `meta/specs/FORMATS.md:55-59` (R-7), `meta/specs/FORMATS.md:92-95` (R-12), `meta/specs/FORMATS.md:138` (R-16), `meta/specs/FORMATS.md:197` (R-22)
- `meta/specs/TESTING.md:124-134` (V-10, V-11)
- PA-053 and PA-081 headings exist in `meta/DECISIONS.md` (lines 450 and 565).
- The corpora row is at `meta/roadmap/0.0/0.0.1_tools/step5.patch:80`.

## What would change this
**Would-change-the-plan-if: a corpus's current version judges a case differently from the version a cycle planned against.**
- **toml-test: it did, in two ways.**
  - **TOML 1.1 relaxation (verified from the changelog).** The planned version is v1.0.0 (`meta/specs/FORMATS.md:63`). If the vendored commit is run under the 1.1 file list or `-toml=latest`, inputs that 1.0 rejects (multi-line inline tables, trailing comma in an inline table, `\xHH`, `\e`, seconds-less times) become valid cases. R-12 requires both `valid/` and `invalid/` to pass, and R-10/R-11 plus the TOML cycle's `Fault(BadTable)` handling assume 1.0 grammar. Inference (mine): the answer depends on which file list PROVENANCE.md records. It should record `files-toml-1.0.0` and the commit, so that a 1.1 case cannot silently enter the gate (PA-081's provenance rule).
  - **BOM valid cases removed.** `utf8-bom-01` and `utf8-bom-02` were deleted from both manifests on 2026-09-15. The project now treats a leading BOM as implementation-defined. Inference (mine): a vendored commit from before `0d1c92e` would require acceptance of a leading BOM, and a commit from after would impose no verdict. Decide which commit to vendor and state it. PA-053's exact pass count would change by the two removed cases.
- **JSONTestSuite: no change found.** V-10 and R-7 are unaffected. The `i_` verdicts are recorded by the library, not by the corpus.
- **yaml-test-suite: no verdict change found.** The newest data tag is 2022-01-17. V-11's committed per-case filter list must be written against that tag's case identifiers. The README warns the `data` branch is force-pushed, so vendor a dated tag, not a branch commit.
- **CSVW: no change found** in the repository-level latest commit. The per-case state of `tests/` was not diffed.

## Confidence and gaps
**Confidence: medium.** Versions, hashes and dates come from the GitHub API and release notes, which are primary. For toml-test and TOML there are two independent primaries (the project's releases, README and commits, plus the toml-lang/toml changelog), and for the TOML-version claim there are three. The security-sensitivity rule asks for two primaries on each claim, and that is not met everywhere.
- **JSONTestSuite, yaml-test-suite and CSVW have only one primary each** (their own repository), and the standards bodies do not publish a competing version for them.
- **Unresolved: toml-test's default TOML version.** The v2.0.0 release notes say 1.1; the current README says 1.0. I did not read the code. Pass `-toml=1.0` explicitly, or use the `files-toml-1.0.0` list, so the gate does not depend on the default.
- **Not verified:**
  - Which YAML version the yaml-test-suite encodes. Its README does not say. The 1.2 core schema in FORMATS.md §4 cannot be confirmed from the corpus.
  - Case-level differences between `files-toml-1.0.0` and `files-toml-1.1.0`. I did not enumerate them.
  - Whether the CSVW `tests/` directory changed after the 2016 final release.
  - The "latest commit" for the yaml-test-suite is the API default, which I assumed is `main`. The fetch tool could not confirm the branch.
- The fetch budget (20) was used up. The `data` branch contents, the CSVW test manifest after character 100,000, and the toml-test v2.2.0 added test were not opened.
- This digest is stale for security purposes after 2027-01-14 (90 days).
