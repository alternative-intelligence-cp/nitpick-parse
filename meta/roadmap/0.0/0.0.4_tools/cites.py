#!/usr/bin/env python3
r"""cites.py -- the citation census of the text 0.0.4's merge freezes (T18fix, (CC); management_10's ruling of
2026-10-31 07:54 and nitpick-libs_35's C1, C2, E2 and N1), its four gaps fixed in parse's next text round (T19, (CP):
T18v2's finding 1, as nitpick-libs_35 disposed of it at 10:00:52). A census, not a completeness check: the grep finds
the citation forms below and nothing else, and every hit is then read by hand against its cited line (`cites.tsv`).

    python3 -B cites.py run    <base> <tip>                 # every hit, its place and form; the excluded ones apart
    python3 -B cites.py record <base> <tip> <cites.tsv> <at> # the hits against the record's rows marked <at>
    python3 -B cites.py plants <cites_plants.tsv>           # the planted twins, each through the census's own reader

WHAT IT READS: `git diff -U0 <base> <tip>` of every `meta/roadmap/0.0/0.0.4_tools/step*.patch`, inside this
repository (`git -C`, the repository this file sits in), and every line that diff adds after its first hunk header.
Each hit's site is the patch and its line at <tip>. Its PLACE (nitpick-libs_35's C1): PATCH-ADDED where the patch line
begins `+` and is not a header, the text the merge freezes, a new claim; CONTEXT for every other patch line -- context
(` `), a hunk line (`@@`), a removed line (`-`) or a file header -- existing tree text, re-shown because a hunk moved.
A patch line's HEADER is read from the whole patch at <tip>: a `diff --git` line and every line after it up to its
first `@@` (`index`, a mode line, `--- a/...` and `+++ b/...`). A text line the patch adds or removes that begins
`++ `, `-- `, `+++ ` or `--- ` is no header, and is read as what it is.

THE FORMS, each a regular expression over one patch line, every one matched case-insensitively ("Item 11", `pd-191`):
  rule      \b(B|PA|PD|S|G|D|SK|W)-[0-9]{1,4}\b  -- management_10's floor; a `@@PD-n@@` placeholder among them
  open      \bO-N[0-9]+\b                       -- an open question (C2)
  section   §\s?[0-9][0-9.]*                    -- a document's section (C2)
  item      \bitems? [0-9]+\b                   -- an item of a list (C2's "item n", its plural too)
  code      \bNITPICK-[A-Z]+-[0-9]+\b           -- a compiler diagnostic
  ruling    \brulings?\b                        -- a seat's ruling
  plan      \b[0-9]+\.[0-9]+(\.[0-9]+)?'s (plan|page|example|record)\b -- a cycle's plan, page or record, or the
            possessive alone where it ends its line (`1.0.3's` / `example`)
  document  a `*.md` file whose name is letters and `_` (`BUILD.md`, `src/README.md`), cited whole
THE EXCLUSIONS, each with its reason; `plants` runs a twin of each branch, and a twin where its reason stops:
  X1  a compiler diagnostic, named as the output it is: its code, always; and the quotation that follows the code,
      `("...")` or `"..."`, opening within 40 characters with no `(` or `"` between, only where it is THAT code's
      message: every part of its quoted words, cut at an elision (`…`), is in a message 0.0.4.md's record prints for
      that code at <tip> (a line `NITPICK-X-n <file>:<line>:<col>: <message>`, §1's items 11 and 12, re-run IDENTICAL
      by T18v). Each part of a quotation that runs on to the next line is read on its own line. A quotation that is
      not the code's message -- the plan's own words, another code's message -- keeps every citation in it, and a
      citation the plan writes itself, outside a quotation, is counted (nitpick-libs_35's N1).
  X2  a document named in a patch's file header (above): a path, not a citation.
  X3  a document followed by a rule, open question or section of its own (`BUILD.md` B-16, `PLAYBOOK.md` §10): one
      citation, counted once, by the rule's form. OWN below names each rule form's documents; a section belongs to
      any document. A document followed by another document's rule (`BUILD.md` S-6) is counted, and so is the rule.
Exit: 0 when it ran (`run`), when every hit has exactly one row and every row a hit, and no row is OVER-REACHES,
unclassed, or SUPPORTS without its quoted words (`record`), and when every plant reads exactly as its row says
(`plants`); 1 on any of those; 2 when the tree cannot be read. A row of another <at> whose class reads `=` is read as
the `tip` row of the same site and token.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
PLAN = "meta/roadmap/0.0/0.0.4.md"
PREFIXES = ("B", "PA", "PD", "S", "G", "D", "SK", "W")
RULE = r"(?:%s)-[0-9]{1,4}" % "|".join(PREFIXES)
FORMS = [
    ("rule", re.compile(r"\b%s\b" % RULE, re.I)),
    ("open", re.compile(r"\bO-N[0-9]+\b", re.I)),
    ("section", re.compile(r"§\s?[0-9][0-9.]*")),
    ("item", re.compile(r"\bitems? [0-9]+\b", re.I)),
    ("code", re.compile(r"\bNITPICK-[A-Z]+-[0-9]+\b", re.I)),
    ("ruling", re.compile(r"\brulings?\b", re.I)),
    ("plan", re.compile(r"\b[0-9]+\.[0-9]+(?:\.[0-9]+)?'s(?: (?:plan|page|example|record)\b|\s*$)", re.I)),
    ("document", re.compile(r"[\w./-]*\b[A-Z][A-Z_]+\.md\b", re.I)),
]
CODE = FORMS[4][1]
# X3's "its own": the documents each rule form is declared in. The compiler's D-n are in its DECISIONS.md, parse's
# in VALUE_MODEL.md; W-n are parse's WRITER_MODEL.md or the workbench's WORKSTREAMS.md; SK-n a decision log's.
OWN = {"B": ("BUILD.md",), "PA": ("DECISIONS.md",), "PD": ("DECISIONS.md",), "S": ("SAFETY.md",),
       "G": ("PLUGIN_MODEL.md",), "D": ("VALUE_MODEL.md", "DECISIONS.md"), "SK": ("DECISIONS.md",),
       "W": ("WRITER_MODEL.md", "WORKSTREAMS.md"), "O-N": ("OPEN_QUESTIONS.md",)}
FOLLOWED = re.compile(r"`?(?:'s)?\s*(?:(§)|(%s)-[0-9]|(O-N)[0-9])" % "|".join(PREFIXES), re.I)
OUTPUT = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) \S+:[0-9]+:[0-9]+: (.+)$")
CLASSES = ("SUPPORTS", "OVER-REACHES", "POINTER")


def messages(text):
    """Every message the plan's record prints, by its code: the lines `NITPICK-X-n <file>:<l>:<c>: <message>`."""
    out = {}
    for l in text.split("\n"):
        m = OUTPUT.match(l.strip())
        if m:
            out.setdefault(m.group(1).upper(), set()).add(m.group(2))
    return out


def is_message(code, quoted, msgs):
    parts = [p.strip(" \t+-") for p in re.split(r"…|\.\.\.", quoted) if p.strip(" \t+-")]  # a patch line's marker off
    return bool(parts) and all(any(p in m for m in msgs.get(code.upper(), ())) for p in parts)


def headers(lines):
    """The 1-based numbers of a patch's header lines: each `diff --git` line and every line after it to its first
    `@@`."""
    out, inside = set(), False
    for i, l in enumerate(lines, 1):
        if l.startswith("diff --git "):
            inside = True
            out.add(i)
        elif inside and l.startswith("@@"):
            inside = False
        elif inside:
            out.add(i)
    return out


def place(body, header):
    if header:
        return "CONTEXT", "header"
    if body.startswith("+"):
        return "PATCH-ADDED", "added"
    if body.startswith("@@"):
        return "CONTEXT", "hunk"
    if body.startswith("-"):
        return "CONTEXT", "removed"
    return "CONTEXT", "context"


def own(doc, prefix):
    return os.path.basename(doc).upper() in (o.upper() for o in OWN.get(prefix.upper(), ()))


def match_line(body, run_on, header, msgs):
    """Every form's hits on one patch line: (counted, dropped, run_on). A dropped hit carries its exclusion. `run_on`
    is the quotation a code's line left open, (code, closer), or None."""
    spans = []                                   # X1's spans: a diagnostic's code, and its quoted message
    if run_on:                                   # a quotation run on from the line before
        code, closer = run_on
        close = body.find(closer)
        end = len(body) if close < 0 else close + len(closer)
        if is_message(code, body[:len(body) if close < 0 else close], msgs):
            spans.append((0, end))
        run_on = (code, closer) if close < 0 else None
    for m in CODE.finditer(body):
        spans.append((m.start(), m.end()))
        q = body.find('"', m.end())
        if q < 0:
            continue
        opener = '("' if q > 0 and body[q - 1] == "(" else '"'
        between = body[m.end():q - len(opener) + 1]
        if len(between) > 40 or "(" in between or '"' in between:
            continue
        closer = '")' if opener == '("' else '"'
        close = body.find(closer, q + 1)
        quoted = body[q + 1:len(body) if close < 0 else close]
        if is_message(m.group(0), quoted, msgs):
            spans.append((q - len(opener) + 1, len(body) if close < 0 else close + len(closer)))
            run_on = (m.group(0), closer) if close < 0 else None
    counted, dropped = [], []
    for form, rx in FORMS:
        for m in rx.finditer(body):
            tok = m.group(0).rstrip(".")
            f = FOLLOWED.match(body, m.end()) if form == "document" else None
            if any(a <= m.start() < b for a, b in spans):
                dropped.append((form, tok, "X1"))
            elif form == "document" and header:
                dropped.append((form, tok, "X2"))
            elif f and (f.group(1) or own(tok, f.group(2) or f.group(3))):
                dropped.append((form, tok, "X3"))
            else:
                counted.append((form, tok))
    return counted, dropped, run_on


def read_diff(text):
    """The lines a `git diff -U0` adds, after its first hunk header: (line at the new side, body, a hunk's first)."""
    out, n, first = [], None, False
    for l in text.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", l)
        if m:
            n, first = int(m.group(1)), True
            continue
        if n is None or not l.startswith("+"):
            continue
        out.append((n, l[1:], first))
        n, first = n + 1, False
    return out


def scan(entries, heads, msgs):
    """Each read line's (n, body, place, kind, counted, dropped), a quotation's run-on reset at every hunk."""
    out, run_on = [], None
    for n, body, first in entries:
        if first:
            run_on = None
        pl, kind = place(body, n in heads)
        counted, dropped, run_on = match_line(body, run_on, n in heads, msgs)
        out.append((n, body, pl, kind, counted, dropped))
    return out


def git(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr)
        sys.exit(2)
    return r.stdout


def census(base, tip):
    files = sorted(f for f in git("ls-tree", "--name-only", tip, "meta/roadmap/0.0/0.0.4_tools/").split()
                   if re.search(r"/step[^/]*\.patch$", f))
    if not files:
        sys.stderr.write("no step*.patch at %s\n" % tip)
        sys.exit(2)
    msgs = messages(git("show", "%s:%s" % (tip, PLAN)))
    hits, drops, added = [], [], {}
    for f in files:
        name = f.rsplit("/", 1)[1]
        heads = headers(git("show", "%s:%s" % (tip, f)).split("\n"))
        lines = scan(read_diff(git("diff", "-U0", base, tip, "--", f)), heads, msgs)
        added[name] = len(lines)
        for n, _b, pl, kind, counted, dropped in lines:
            for form, tok in counted:
                hits.append(("%s:%d" % (name, n), pl, kind, form, tok))
            for form, tok, why in dropped:
                drops.append(("%s:%d" % (name, n), pl, kind, form, tok, why))
    return hits, drops, added


def counts(hits):
    out = {}
    for site, pl, _k, _f, _t in hits:
        name = site.split(":")[0]
        c = out.setdefault(name, {"lines": set(), "hits": 0, "PATCH-ADDED": [set(), 0]})
        c["lines"].add(site)
        c["hits"] += 1
        if pl == "PATCH-ADDED":
            c["PATCH-ADDED"][0].add(site)
            c["PATCH-ADDED"][1] += 1
    return out


def report(base, tip):
    hits, drops, added = census(base, tip)
    print("cites.py run %s %s: %d added line(s) read in %d patch(es)" % (base, tip, sum(added.values()), len(added)))
    c = counts(hits)
    tl = th = pl = ph = 0
    for name in sorted(added):
        x = c.get(name, {"lines": set(), "hits": 0, "PATCH-ADDED": [set(), 0]})
        print("  %-14s %3d added line(s); %3d line(s), %3d hit(s); PATCH-ADDED %3d line(s), %3d hit(s)"
              % (name, added[name], len(x["lines"]), x["hits"], len(x["PATCH-ADDED"][0]), x["PATCH-ADDED"][1]))
        tl += len(x["lines"]); th += x["hits"]; pl += len(x["PATCH-ADDED"][0]); ph += x["PATCH-ADDED"][1]
    print("  %-14s %3d line(s), %3d hit(s); PATCH-ADDED %3d line(s), %3d hit(s)" % ("all", tl, th, pl, ph))
    by = {}
    for h in hits:
        by[h[3]] = by.get(h[3], 0) + 1
    print("  by form: " + ", ".join("%s %d" % (f, by.get(f, 0)) for f, _ in FORMS))
    for h in hits:
        print("HIT\t%s\t%s\t%s\t%s\t%s" % h)
    for d in drops:
        print("DROPPED\t%s\t%s\t%s\t%s\t%s\t%s" % d)
    return hits


def record(base, tip, path, at):
    hits, _d, _a = census(base, tip)
    try:
        rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")
                if l.strip() and not l.startswith("#")]
    except OSError as e:
        sys.stderr.write("%s\n" % e)
        sys.exit(2)
    head, every = rows[0], rows[1:]
    rows = [r for r in every if r[0] == at]
    tips = {(r[1], r[4]): r for r in every if r[0] == "tip"}
    bad = []
    want = {}
    for h in hits:
        want[(h[0], h[1], h[3], h[4])] = want.get((h[0], h[1], h[3], h[4]), 0) + 1
    have = {}
    for r in rows:
        if len(r) != len(head):
            bad.append("a row with %d field(s), not %d: %s" % (len(r), len(head), "\t".join(r)))
            continue
        k = (r[1], r[2], r[3], r[4])
        have[k] = have.get(k, 0) + 1
        cls, quote = r[5], r[7]
        if cls == "=":                              # a base row read as the tip's row at the same site and token
            t = tips.get((r[1], r[4]))
            if not t:
                bad.append("%s %s: '=' names no tip row" % (r[1], r[4]))
                continue
            cls, quote = t[5], t[7]
        if cls not in CLASSES:
            bad.append("%s %s: class %r is none of %s" % (r[1], r[4], cls, ", ".join(CLASSES)))
        elif cls == "OVER-REACHES":
            bad.append("%s %s: OVER-REACHES -- %s" % (r[1], r[4], quote))
        elif cls == "SUPPORTS" and not re.search(r'"[^"]+"', quote):
            bad.append("%s %s: SUPPORTS with no quoted words" % (r[1], r[4]))
    for k in sorted(set(want) | set(have)):
        if want.get(k, 0) != have.get(k, 0):
            bad.append("%s %s %s %s: %d hit(s), %d row(s)" % (k + (want.get(k, 0), have.get(k, 0))))
    print("cites.py record %s %s %s %s: %d hit(s), %d row(s), %d finding(s)" % (base, tip, os.path.basename(path), at,
                                                                              len(hits), len(rows), len(bad)))
    for b in bad:
        print("FINDING " + b)
    return 1 if bad else 0


def plants(path):
    """Each plant group -- a row, and the rows after it whose names end `+cont` -- is written as the patch lines a
    `git diff -U0` adds, read by `read_diff`, its headers by `headers` over the group's lines, its messages from this
    tree's 0.0.4.md, and each line's place, counts and drops held to its row."""
    try:
        rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]
        msgs = messages(open(os.path.join(ROOT, PLAN), encoding="utf-8").read())
    except OSError as e:
        sys.stderr.write("%s\n" % e)
        sys.exit(2)
    groups = []
    for r in rows:
        if r[0].endswith("+cont") and groups:
            groups[-1].append(r)
        else:
            groups.append([r])
    bad = 0
    for g in groups:
        bodies = [r[1] for r in g]
        diff = "@@ -0,0 +1,%d @@\n" % len(bodies) + "".join("+%s\n" % b for b in bodies)
        read = {x[0]: x for x in scan(read_diff(diff), headers(bodies), msgs)}
        for i, r in enumerate(g, 1):
            if i not in read:                   # a line the census's reader does not read is a plant not as planted
                bad = 1
                print("FAIL %s: not read" % r[0])
                continue
            _n, _b, pl, kind, counted, dropped = read[i]
            got_p = "%s:%s" % (pl, kind)
            got_c = " ".join("%s:%s" % c for c in counted) or "-"
            got_d = " ".join("%s:%s:%s" % d for d in dropped) or "-"
            ok = (got_p, got_c, got_d) == (r[2], r[3], r[4])
            bad |= not ok
            print("%s %s: %s; counted %s; dropped %s" % ("PASS" if ok else "FAIL", r[0], got_p, got_c, got_d))
    print("cites.py plants: %d plant(s), %s" % (len(rows), "every one as planted" if not bad else "NOT as planted"))
    return 1 if bad else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["run"] and len(a) == 3:
        report(a[1], a[2])
        sys.exit(0)
    if a[:1] == ["record"] and len(a) == 5:
        sys.exit(record(a[1], a[2], a[3], a[4]))
    if a[:1] == ["plants"] and len(a) == 2:
        sys.exit(plants(a[1]))
    sys.stderr.write(__doc__)
    sys.exit(2)
