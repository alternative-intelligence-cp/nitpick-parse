#!/usr/bin/env python3
"""0.0.4 -- the public error count checked by structure, not by a list of words: the tree's `error:` declarations
parsed (the management seat's ruling of 2026-10-31 05:24, on PD-191), and every claim on a corrected subject keyed on
the subject and failing when bare (T16v2's finding 2; the management seat's rulings of 04:24 and 04:41; the workbench
`PLAYBOOK.md` §12's twins bullet, tightened 2026-10-31).

    python3 -B claims.py decls   "$REPO"              # the declarations, against PD-191's module
    python3 -B claims.py claims  "$REPO" [<row> ...]  # every row of claims_rows.tsv over the tree, or those named
    python3 -B claims.py control "$REPO" [<name> ...] # the controls: each row's base claim, the plants, the decls cases

Each exits 0 when it finds nothing, 1 on any finding (a control: on any case not as planted), and 2 when the tree
cannot be read -- git missing or failing, or a file the check reads by name absent -- so a check that read nothing
never passes in silence.

DECLS reads every `.npk` file git lists in the tree, tracked or untracked and not ignored (`git ls-files` and `git
ls-files --others --exclude-standard`): the library's modules under `src/`, the tests and fixtures under `tests/`, and
any other. Each is read through the tree's own `harness/lexical.py`, comments and strings blanked, so a word in a
comment is no declaration; a declaration is `error:<Name>`, `pub` or not, keyed by the file's `mod:` and the name.
PD-191's module is `src/nparse/nparse.npk`, `mod:nparse`. While it is absent, no file declares an `error:`. Once it
exists it declares exactly the names of `meta/specs/SAFETY.md` §3's table, each once, and no other file declares
one. A file that declares one on purpose -- a probe of the REACH or of G-7 -- is listed in `decls_listed.tsv` beside
this script, `path<TAB>reason`, and printed with its reason; a listed file that is absent or declares nothing is a
finding too.

CLAIMS reads every file git lists, tracked or untracked, but the patches, the `.npk` sources, `LICENSE` and the
research digests, each line through the stale-claim sweep's transform (`../tools/sweep.py`); a row's PATHS, `sweep`,
reads what the sweep reads, those files but the cycle 0.0 plans, and any other value is a pattern a path must match.
A Markdown file's fenced blocks are not read, since a command or its output is no claim, and a cycle 0.0 plan is read
up to its `## Execution record`, which its worker writes after. A file is cut into PARAGRAPHS -- a blank line, a heading, a list item and a table row each start
one -- and a paragraph into SENTENCES, each joined across its line breaks. A row of `claims_rows.tsv`,
`row<TAB>paths<TAB>subject<TAB>claim<TAB>anchor<TAB>base`, names its subject by what the claim is about: a sentence is a
CANDIDATE when its claim pattern matches it and its subject pattern matches it or the sentence before it in the same
paragraph, so a claim that does not repeat its subject is still read. A candidate is CARRIED when the anchor --
the correction's own terms -- stands in the sentence, in a dated note in the same paragraph (a parenthesis opening
within forty characters of a date) or in one that opens the block beneath its block (a block is a run of lines
between blank ones), or in the heading of the `###` section it stands in, or in a dated note there;
CLASSED when `claims_listed.tsv`, `row<TAB>path<TAB>fragment<TAB>class<TAB>reason`, holds its path and a fragment of
its sentence; and BARE otherwise, which is a finding. A listed line no candidate holds is a finding (STALE). In a
pattern, `{PD-n}` stands for the decision's number in the tree and its placeholder, `PA-<base + rank>` by
`../tools/decisions.txt` or `@@PD-n@@`, so no file of the plan writes a number past the base.

CONTROL runs, per row, the check over the row's BASE, `<commit>:<path>:<fragment>`, read from git at that commit,
the base claim there, which must be reported BARE with the check's exit non-zero; then each plant of
`claims_plants.tsv`, `row<TAB>name<TAB>expect<TAB>text` (`\\n` a line break), planted as `planted/<name>.md` beside
the tree's files, in memory: a `bare` plant must be reported BARE, with the exit 1, and a `carried` one, the same
claim with its correction, must not be; and the hit rate. Then the decls cases of `DECLS_CASES` below, each an edit
to the tree's `.npk` texts in memory and the exit it must give. Nothing is written anywhere.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import apply  # noqa: E402  -- the decision numbers, as the patches are given them
import sweep  # noqa: E402  -- the sweep's files and its transform

DECLARING, MODULE = "src/nparse/nparse.npk", "nparse"
NOTE = re.compile(r"\((?:[^()]{0,40}?)\b\d{4}-\d{2}-\d{2}\b")
SENTENCE_END = re.compile(r"(?<=[.;!?])\s+(?=[A-Z0-9(\"'])")
STARTS = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|\||#+\s)")
STARTS_CODE = re.compile(r"^\s*(?:#+\s*|//+\s*)?(?:[-*+]\s|\d+[.)]\s|\|)")
HEADING3 = re.compile(r"^\s*#{3,}\s")
PLANS = re.compile(r"(^|/)meta/roadmap/(done/)?0\.0/")
SKIP = re.compile(r"\.patch$|\.npk$|^LICENSE$")
DECL = re.compile(r"(?<![\w.])error\s*:\s*([A-Za-z_]\w*)")
MOD = re.compile(r"\bmod\s*:\s*(\w+)")


class Unreadable(Exception):
    pass


def git_files(root, git="git"):
    """Every file git lists in the tree, tracked or untracked and not ignored; Unreadable when git cannot say."""
    out = []
    for extra in ([], ["--others", "--exclude-standard"]):
        try:
            r = subprocess.run([git, "-C", root, "ls-files", *extra], capture_output=True, text=True)
        except OSError as e:
            raise Unreadable("git could not be run: %s" % e.strerror)
        if r.returncode != 0:
            raise Unreadable("git ls-files exited %d" % r.returncode)
        out += [f for f in r.stdout.split("\n") if f and not f.endswith("/")]
    return sorted(set(out))


def read(root, f):
    with open(os.path.join(root, f), "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


def tsv(name, width):
    rows = []
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip() or line.startswith("#"):
                continue
            cells = line.rstrip("\n").split("\t")
            if len(cells) != width:
                raise SystemExit("STOP: %s:%d has %d cell(s), not %d" % (name, n, len(cells), width))
            rows.append(cells)
    return rows


# ---- DECLS ------------------------------------------------------------------------------------------------------

def spec_names(safety):
    sec = safety[safety.index("## 3."):safety.index("## 4.")]
    return sorted(set(re.findall(r"^\| `(E\w+)` \|", sec, re.M)))


def check_decls(texts, names, listed, blank):
    """texts {path: raw}, every .npk read; names, SAFETY.md §3's; listed {path: reason} -> (report, findings)."""
    decls = []
    for p in sorted(texts):
        b = blank(texts[p])
        m = MOD.search(b)
        for d in DECL.finditer(b):
            decls.append((p, b.count("\n", 0, d.start()) + 1, m.group(1) if m else "?", d.group(1)))
    bad, present = [], DECLARING in texts
    if present:
        m = MOD.search(blank(texts[DECLARING]))
        if not m or m.group(1) != MODULE:
            bad.append("%s: its `mod:` is %s, not `%s` (PD-191)" % (DECLARING, "`%s`" % m.group(1) if m else "absent",
                                                                     MODULE))
        mine = [(n, line) for p, line, _, n in decls if p == DECLARING]
        for n, line in mine:
            if n not in names:
                bad.append("%s:%d: `%s.%s` -- a name SAFETY.md §3's table does not hold" % (DECLARING, line, MODULE, n))
            elif [x for x, _ in mine].count(n) > 1:
                bad.append("%s:%d: `%s.%s` declared again" % (DECLARING, line, MODULE, n))
        for n in names:
            if n not in [x for x, _ in mine]:
                bad.append("%s: does not declare `%s`, a name of SAFETY.md §3's table" % (DECLARING, n))
    seen = []
    for p, line, mod, n in decls:
        if p == DECLARING:
            continue
        if p in listed:
            seen.append("  listed %s:%d: `%s.%s` -- %s" % (p, line, mod, n, listed[p]))
        elif present:
            bad.append("%s:%d: `%s.%s` declared outside %s" % (p, line, mod, n, DECLARING))
        else:
            bad.append("%s:%d: `%s.%s` declared while %s is absent, when no file declares one" % (p, line, mod, n,
                                                                                               DECLARING))
    for p in sorted(listed):
        if p not in texts:
            bad.append("decls_listed.tsv: %s is not a .npk file of the tree" % p)
        elif not [d for d in decls if d[0] == p]:
            bad.append("decls_listed.tsv: %s declares no `error:`" % p)
    where = {"src": 0, "tests": 0}
    for p in texts:
        k = p.split("/")[0]
        where[k if k in where else "elsewhere"] = where.get(k if k in where else "elsewhere", 0) + 1
    keyed = ", ".join("%s.%s (%s:%d)" % (mod, n, p, line) for p, line, mod, n in decls) or "none"
    report = ["decls: %d .npk file(s) read -- src/ %d, tests/ %d, elsewhere %d; SAFETY.md §3's names: %s; %s: %s"
              % (len(texts), where["src"], where["tests"], where.get("elsewhere", 0), ", ".join(names) or "none",
                 DECLARING, "present" if present else "absent"),
              "decls: declared, keyed by (module, name): " + keyed,
              "decls: listed: %d" % len(listed)] + seen
    return report, bad


def lexical_blank(root):
    sys.path.insert(0, os.path.join(root, "harness"))
    try:
        import lexical
    finally:
        sys.path.pop(0)
    return lexical.blank


def decls_inputs(root, git="git"):
    files = [f for f in git_files(root, git) if f.endswith(".npk") and os.path.isfile(os.path.join(root, f))]
    if not files:
        raise Unreadable("git lists no .npk file")
    p = os.path.join(root, "meta", "specs", "SAFETY.md")
    if not os.path.isfile(p):
        raise Unreadable("meta/specs/SAFETY.md is absent")
    listed = {p_: why for p_, why in tsv("decls_listed.tsv", 2)}
    return {f: read(root, f) for f in files}, spec_names(read(root, "meta/specs/SAFETY.md")), listed


def decls(root):
    try:
        texts, names, listed = decls_inputs(root)
    except Unreadable as e:
        print("decls: CANNOT READ the tree -- %s" % e)
        return 2
    report, bad = check_decls(texts, names, listed, lexical_blank(root))
    print("\n".join(report))
    for b in bad:
        print("FAIL decls: " + b)
    return 1 if bad else 0


# ---- CLAIMS -----------------------------------------------------------------------------------------------------

def expand(rx, numbers):
    def one(m):
        pd = "PD-" + m.group(1)
        if pd not in numbers:
            raise SystemExit("STOP: claims_rows.tsv names {%s}, which decisions.txt does not number" % pd)
        return r"(?:\b%s\b|@@%s@@)" % (numbers[pd], pd)
    return re.sub(r"\{PD-(\d+)\}", one, rx)


def rows(names=None):
    numbers = apply.numbers()
    out = []
    for name, paths, subj, claim, anchor, base in tsv("claims_rows.tsv", 6):
        if names and name not in names:
            continue
        out.append({"row": name, "paths": paths, "subject": re.compile(expand(subj, numbers), re.I),
                    "claim": re.compile(expand(claim, numbers), re.I),
                    "anchor": re.compile(expand(anchor, numbers), re.I), "base": base})
    if names and len(out) != len(set(names)):
        raise SystemExit("STOP: no row named %s" % ", ".join(sorted(set(names) - {r["row"] for r in out})))
    return out


def paragraphs(lines, md=True):
    """[(the paragraph's lines as (number, text), the `###` heading it stands under or '', its block)]: a BLOCK is a
    run of lines between blank ones, and a paragraph one block's list item, table row, heading or prose run. Outside
    Markdown a `#` opens a comment, not a heading: a comment's lines are one run, and so is a comment marker alone."""
    out, cur, head, block = [], [], "", 0
    starts = STARTS if md else STARTS_CODE
    for n, line in enumerate(lines, 1):
        blank_line = not line.strip() or (not md and re.fullmatch(r"\s*(#+|//+)\s*", line))
        if blank_line or starts.match(line):
            if cur:
                out.append((cur, head, block))
            cur = []
            if blank_line:
                block += 1
                continue
            if md and HEADING3.match(line):
                head = line
            elif md and re.match(r"^\s*#{1,2}\s", line):
                head = ""
        cur.append((n, line))
    if cur:
        out.append((cur, head, block))
    return out


def carried_by_note(text, anchor):
    return any(anchor.search(text[m.start():]) for m in NOTE.finditer(text))


def prose(path, text):
    """A file's lines as CLAIMS reads them: in Markdown a fenced block's lines blank, since a command or its output is
    no claim; and in a cycle 0.0 plan nothing from its `## Execution record` on, the worker's, written after."""
    lines = text.split("\n")
    if path.endswith(".md"):
        fenced = False
        for k, line in enumerate(lines):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                lines[k] = ""
            elif fenced:
                lines[k] = ""
    if PLANS.search(path):
        for k, line in enumerate(lines):
            if line.startswith("## Execution record"):
                lines = lines[:k]
                break
    return lines


def candidates(row, lines, md=True):
    """[(line, sentence, state)] with state 'carried' or 'bare' -- before the listed lines are read"""
    out, paras = [], paragraphs(lines, md)
    joined = [sweep.joined([t for _, t in pl]) for pl, _, _ in paras]
    secs, beneath = {}, set()
    for k, (pl, head, block) in enumerate(paras):
        if head:
            secs[head] = secs.get(head, "") + " " + joined[k][0]
        first = k == 0 or paras[k - 1][2] != block
        if first and NOTE.match(joined[k][0]) and row["anchor"].search(joined[k][0]):
            beneath.add(block - 1)
    for k, (plines, head, block) in enumerate(paras):
        text, where = joined[k]
        if not text:
            continue
        sec = secs.get(head, "")
        sec_carries = bool(head) and (row["anchor"].search(sweep.strip(head)) or carried_by_note(sec, row["anchor"]))
        para_carries = carried_by_note(text, row["anchor"]) or block in beneath
        spans, pos = [], 0
        for m in SENTENCE_END.finditer(text):
            spans.append((pos, text[pos:m.start()]))
            pos = m.end()
        spans.append((pos, text[pos:]))
        for i, (start, s) in enumerate(spans):
            c = row["claim"].search(s)
            if not c or not (row["subject"].search(s) or (i and row["subject"].search(spans[i - 1][1]))):
                continue
            line = plines[where[start + c.start()] - 1][0]
            ok = row["anchor"].search(s) or para_carries or sec_carries
            out.append((line, s, "carried" if ok else "bare"))
    return out


def check_claims(texts, therows, listed):
    """texts {path: raw}; listed [(row, path, fragment, class, reason)] -> (report, findings, every candidate as
    (row, path, line, sentence, state))"""
    report, bad, every = [], [], []
    for row in therows:
        mine = [x for x in listed if x[0] == row["row"]]
        used = set()
        found = []
        if row["paths"] == "sweep":
            read_ = [p for p in sorted(texts) if not PLANS.search(p)]
        else:
            read_ = [p for p in sorted(texts) if re.search(row["paths"], p)]
        for p in read_:
            for line, s, state in candidates(row, prose(p, texts[p]), p.endswith(".md")):
                if state == "bare":
                    for k, (_, lp, frag, cls, _) in enumerate(mine):
                        if lp == p and frag in s:
                            state = "classed " + cls
                            used.add(k)
                            break
                found.append((p, line, s, state))
        n = {k: sum(1 for x in found if x[3].split()[0] == k) for k in ("carried", "classed", "bare")}
        report.append("%s: %d candidate(s) in %d file(s) of %d read -- %d carried, %d classed, %d bare"
                      % (row["row"], len(found), len({x[0] for x in found}), len(read_), n["carried"], n["classed"],
                         n["bare"]))
        for p, line, s, state in found:
            every.append((row["row"], p, line, s, state))
            report.append("  %s %s:%d" % (state, p, line))
            if state == "bare":
                bad.append("%s: BARE %s:%d -- %s" % (row["row"], p, line, s[:160]))
        for k, (_, lp, frag, cls, _) in enumerate(mine):
            if k not in used:
                bad.append("%s: STALE claims_listed.tsv: %s %r -- no bare candidate holds it" % (row["row"], lp, frag))
    return report, bad, every


def claim_texts(root):
    out = {}
    files = [f for f in git_files(root) if not SKIP.search(f) and os.path.isfile(os.path.join(root, f))]
    if not files:
        raise Unreadable("git lists no file")
    for f in files:
        t = read(root, f)
        if not sweep.DIGEST.match(t.split("\n", 1)[0]):
            out[f] = t
    return out


def claims(root, names):
    try:
        texts = claim_texts(root)
    except Unreadable as e:
        print("claims: CANNOT READ the tree -- %s" % e)
        return 2
    report, bad, _ = check_claims(texts, rows(names), tsv("claims_listed.tsv", 5))
    print("claims: %d file(s) read -- every tracked or added file but the patches, sources, LICENSE and the research "
          "digests; a row of paths `sweep` reads them but the cycle 0.0 plans" % len(texts))
    print("\n".join(report))
    for b in bad:
        print("FAIL claims: " + b)
    return 1 if bad else 0


# ---- CONTROL ----------------------------------------------------------------------------------------------------

def texts_at(root, commit):
    """The files CLAIMS reads, as they stood at a commit, read from git."""
    r = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", commit], capture_output=True, text=True)
    if r.returncode != 0:
        raise Unreadable("git ls-tree %s exited %d" % (commit, r.returncode))
    out = {}
    for f in r.stdout.split("\n"):
        if not f or SKIP.search(f):
            continue
        t = subprocess.run(["git", "-C", root, "show", "%s:%s" % (commit, f)], capture_output=True).stdout
        t = t.decode("utf-8", errors="replace")
        if not sweep.DIGEST.match(t.split("\n", 1)[0]):
            out[f] = t
    return out


# name, what it plants, edits {path: (old, new)} to the .npk texts (old None: append; new None: remove the file),
# a listed table to use instead of decls_listed.tsv, or None, and the exit it must give
DECLS_CASES = [
    ("format-declares-its-own", "a format declaring an `error:` of its own",
     {"src/format/format.npk": (None, "\npub error:EParseState;\n")}, None, 1),
    ("third-name-in-the-module", "a third name in the declaring module",
     {DECLARING: (None, "pub error:EParseOverflow;\n")}, None, 1),
    ("state-declared-outside", "`EParseState` declared outside the module, in `core`",
     {"src/core/core.npk": (None, "\npub error:EParseState;\n")}, None, 1),
    ("encode-declared-outside", "`EParseEncode` declared outside the module, in `emit`",
     {"src/emit/emit.npk": (None, "\npub error:EParseEncode;\n")}, None, 1),
    ("name-missing-from-the-module", "the module without `EParseEncode`",
     {DECLARING: ("pub error:EParseEncode;\n", "")}, None, 1),
    ("module-misnamed", "the module's `mod:` another name",
     {DECLARING: ("mod:nparse;", "mod:errors;")}, None, 1),
    ("a-declaration-before-the-module", "the module absent and `doc` declaring `EParseState`",
     {DECLARING: ("", None), "src/doc/doc.npk": (None, "\npub error:EParseState;\n")}, None, 1),
    ("no-declaration-before-the-module", "the module absent and no declaration anywhere",
     {DECLARING: ("", None)}, None, 0),
    ("a-test-declaring-unlisted", "a unit declaring an identity, not listed",
     {"tests/unit/planted_decl.npk": ("", "mod:planted_decl;\n\npub error:EParseState;\n")}, None, 1),
    ("a-test-declaring-listed", "the same unit, listed with its reason",
     {"tests/unit/planted_decl.npk": ("", "mod:planted_decl;\n\npub error:EParseState;\n")},
     {"tests/unit/planted_decl.npk": "a planted probe"}, 0),
    ("a-stale-listed-line", "a listed file that declares nothing",
     {}, {"src/core/core.npk": "a planted stale line"}, 1),
    ("a-declaration-in-a-comment-or-string", "`error:` in a comment and a string only",
     {"src/format/format.npk": (None, "\n// pub error:EParseOwn;\nfixed string:planted = \"error:EParseOwn\";\n")},
     None, 0),
]


def edited(texts, edits):
    out = dict(texts)
    for p, (old, new) in edits.items():
        if new is None:
            out.pop(p, None)
        elif old is None:
            out[p] = out[p] + new
        elif old == "":
            if p in out:
                raise SystemExit("STOP: the case would add %s, which the tree holds" % p)
            out[p] = new
        else:
            if out[p].count(old) != 1:
                raise SystemExit("STOP: %r occurs %d times in %s" % (old, out[p].count(old), p))
            out[p] = out[p].replace(old, new)
    return out


def control(root, names):
    ok = total = 0

    def verdict(name, good, line):
        nonlocal ok, total
        total += 1
        ok += good
        print("%s %s: %s" % ("ok   " if good else "NOT AS PLANTED", name, line))

    try:
        texts = claim_texts(root)
        dtexts, dnames, dlisted = decls_inputs(root)
    except Unreadable as e:
        print("control: CANNOT READ the tree -- %s" % e)
        return 2
    listed = tsv("claims_listed.tsv", 5)
    plants = tsv("claims_plants.tsv", 4)
    for row in rows():
        if names and row["row"] not in names and not any(n.startswith(row["row"] + ":") for n in names):
            continue
        commit, path, frag = row["base"].split(":", 2)
        try:
            base_texts = texts_at(root, commit)
        except Unreadable as e:
            print("control: CANNOT READ %s -- %s" % (commit, e))
            return 2
        report, bad, every = check_claims(base_texts, [row], listed)
        hit = [x for x in every if x[1] == path and frag in x[3] and x[4] == "bare"]
        verdict("%s: the base claim" % row["row"], bool(hit) and bool(bad),
                "%s at %s: %s; the check's exit there %d (%s)" % (path, commit, "BARE %s:%d" % (path, hit[0][2])
                                                                 if hit else "NOT REPORTED", 1 if bad else 0,
                                                                 report[0].split(" -- ", 1)[1]))
        mine = [p for p in plants if p[0] == row["row"]]
        hits = {"bare": [0, 0], "carried": [0, 0]}
        for _, pname, expect, text in mine:
            planted = "planted/%s.md" % pname
            t = dict(texts)
            t[planted] = text.replace("\\n", "\n") + "\n"
            report, bad, every = check_claims(t, [row], listed)
            mine_bad = [x for x in every if x[1] == planted and x[4] == "bare"]
            good = bool(mine_bad) == (expect == "bare") and (expect != "bare" or bool(bad))
            hits[expect][1] += 1
            hits[expect][0] += good
            if expect == "bare" and not mine_bad:
                carried = [r for r in report if planted in r]
                why = carried[0].split()[0] if carried else "no candidate"
            else:
                why = "BARE" if mine_bad else "not bare"
            verdict("%s: plant %s" % (row["row"], pname), good, "%s, %s; the check's exit %d"
                    % (expect, why, 1 if bad else 0))
        if mine:
            print("%s: hit rate -- %d of %d bare plants reported BARE; %d of %d carried twins passed"
                  % (row["row"], hits["bare"][0], hits["bare"][1], hits["carried"][0], hits["carried"][1]))
    blank = lexical_blank(root)
    for name, what, edits, tab, want in DECLS_CASES:
        if names and "decls:" + name not in names and "decls" not in names:
            continue
        report, bad = check_decls(edited(dtexts, edits), dnames, dlisted if tab is None else tab, blank)
        got = 1 if bad else 0
        verdict("decls: " + name, got == want, "%s -- exit %d%s" % (what, got, (", " + bad[0]) if bad else ""))
    if not names or "decls" in names or "decls:git-missing" in names:
        try:
            decls_inputs(root, git=os.path.join(root, ".internal", "no-such-git"))
            verdict("decls: git-missing", False, "git missing -- the tree was read")
        except Unreadable as e:
            verdict("decls: git-missing", True, "git missing -- exit 2, %s" % e)
    print("control: %d of %d as planted" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("decls", "claims", "control"):
        print(__doc__)
        sys.exit(2)
    root = os.path.realpath(sys.argv[2])
    sys.exit({"decls": lambda: decls(root), "claims": lambda: claims(root, sys.argv[3:]),
              "control": lambda: control(root, sys.argv[3:])}[sys.argv[1]]())
