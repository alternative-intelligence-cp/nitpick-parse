#!/usr/bin/env python3
r"""cites.py -- the citation census of the text 0.0.4's merge freezes (T18fix, (CC); management_10's ruling of
2026-10-31 07:54 and nitpick-libs_35's C1, C2, E2 and N1). A census, not a completeness check: the grep finds the
citation forms below and nothing else, and every hit is then read by hand against its cited line (`cites.tsv`).

    python3 -B cites.py run    <base> <tip>                 # every hit, its place and form; the excluded ones apart
    python3 -B cites.py record <base> <tip> <cites.tsv> <at> # the hits against the record's rows marked <at>
    python3 -B cites.py plants <cites_plants.tsv>           # the exclusions' planted twins, each through the matcher

WHAT IT READS: `git diff -U0 <base> <tip>` of every `meta/roadmap/0.0/0.0.4_tools/step*.patch`, inside this
repository (`git -C`, the repository this file sits in), and every line that diff adds. Each hit's site is the patch
and its line at <tip>. Its PLACE (nitpick-libs_35's C1): PATCH-ADDED where the patch line begins `+` (not `+++ `), the
text the merge freezes, a new claim; CONTEXT for every other patch line -- context (` `), a hunk line (`@@`), a
removed line (`-`) or a file header -- existing tree text, re-shown because a hunk moved.

THE FORMS, each a regular expression over one patch line:
  rule      \b(B|PA|PD|S|G|D|SK|W)-[0-9]{1,4}\b  -- management_10's floor; a `@@PD-n@@` placeholder among them
  open      \bO-N[0-9]+\b                       -- an open question (C2)
  section   §\s?[0-9][0-9.]*                    -- a document's section (C2)
  item      \bitems? [0-9]+\b                   -- an item of a list (C2's "item n", its plural too)
  code      \bNITPICK-[A-Z]+-[0-9]+\b           -- a compiler diagnostic
  ruling    \brulings?\b                        -- a seat's ruling
  plan      \b[0-9]+\.[0-9]+(\.[0-9]+)?'s (plan|page|example|record)\b -- a cycle's plan, page or record, or the
            possessive alone where it ends its line (`1.0.3's` / `example`)
  document  a `*.md` file named in capitals (`BUILD.md`, `src/README.md`), cited whole
THE EXCLUSIONS, each with its reason; `plants` runs a twin of each:
  X1  a compiler diagnostic, named as the output it is: its code, and the quotation that follows the code if one
      does, `("...")`, to its close on the next line if it runs on, every token inside dropped (`D-179` in
      RESOLVE-010's message among them). Each names or quotes an output the record's programs measure (0.0.4.md §1's
      items 11 and 12), re-run IDENTICAL by T18v; a citation the plan writes itself, outside a quotation, is counted
      (nitpick-libs_35's N1).
  X2  a document named in a patch's file header (`diff --git`, `index`, `---`, `+++`): a path, not a citation.
  X3  a document followed by its own rule, open question or section (`BUILD.md` B-16, `PLAYBOOK.md` §10): one
      citation, counted once, by the rule's form.
Exit: 0 when it ran (`run`), when every hit has exactly one row and every row a hit, and no row is OVER-REACHES,
unclassed, or SUPPORTS without its quoted words (`record`), and when every plant drops and counts exactly what its
row says (`plants`); 1 on any of those; 2 when the tree cannot be read. A row of another <at> whose class reads `=`
is read as the `tip` row of the same site and token.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
FORMS = [
    ("rule", re.compile(r"\b(?:B|PA|PD|S|G|D|SK|W)-[0-9]{1,4}\b")),
    ("open", re.compile(r"\bO-N[0-9]+\b")),
    ("section", re.compile(r"§\s?[0-9][0-9.]*")),
    ("item", re.compile(r"\bitems? [0-9]+\b")),
    ("code", re.compile(r"\bNITPICK-[A-Z]+-[0-9]+\b")),
    ("ruling", re.compile(r"\brulings?\b")),
    ("plan", re.compile(r"\b[0-9]+\.[0-9]+(?:\.[0-9]+)?'s(?: (?:plan|page|example|record)\b|\s*$)")),
    ("document", re.compile(r"[\w./-]*\b[A-Z][A-Z_]+\.md\b")),
]
FOLLOWED = re.compile(r"`?'?s?\s*(?:§|(?:B|PA|PD|S|G|D|SK|W)-[0-9]|O-N[0-9])")
HEADER = re.compile(r"^(?:diff --git |index |--- |\+\+\+ )")
CLASSES = ("SUPPORTS", "OVER-REACHES", "POINTER")


def place(body):
    if HEADER.match(body):
        return "CONTEXT", "header"
    if body.startswith("+"):
        return "PATCH-ADDED", "added"
    if body.startswith("@@"):
        return "CONTEXT", "hunk"
    if body.startswith("-"):
        return "CONTEXT", "removed"
    return "CONTEXT", "context"


def match_line(body, open_quote):
    """Every form's hits on one patch line: (counted, dropped, open_quote). A dropped hit carries its exclusion."""
    spans = []                                   # X1's spans: a diagnostic's code and its quoted output
    pos = 0
    if open_quote:                               # a quotation run on from the line before
        close = body.find('")')
        end = len(body) if close < 0 else close + 2
        spans.append((0, end))
        open_quote = close < 0
        pos = end
    for m in FORMS[4][1].finditer(body, pos):
        end = m.end()
        q = body.find('("', end)
        if q >= 0 and body[end:q].count("(") == 0 and len(body[end:q]) <= 40:
            close = body.find('")', q)
            end = len(body) if close < 0 else close + 2
            open_quote = close < 0
        spans.append((m.start(), end))
    counted, dropped = [], []
    for form, rx in FORMS:
        for m in rx.finditer(body):
            tok = m.group(0).rstrip(".")
            if any(a <= m.start() < b for a, b in spans):
                dropped.append((form, tok, "X1"))
            elif form == "document" and HEADER.match(body):
                dropped.append((form, tok, "X2"))
            elif form == "document" and FOLLOWED.match(body, m.end()):
                dropped.append((form, tok, "X3"))
            else:
                counted.append((form, tok))
    return counted, dropped, open_quote


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
    hits, drops, added = [], [], {}
    for f in files:
        n, oq, name = None, False, f.rsplit("/", 1)[1]
        added[name] = 0
        for l in git("diff", "-U0", base, tip, "--", f).splitlines():
            m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", l)
            if m:
                n, oq = int(m.group(1)), False
                continue
            if n is None or not l.startswith("+") or l.startswith("+++ "):
                continue
            body = l[1:]
            pl, kind = place(body)
            counted, dropped, oq = match_line(body, oq)
            for form, tok in counted:
                hits.append(("%s:%d" % (name, n), pl, kind, form, tok))
            for form, tok, why in dropped:
                drops.append(("%s:%d" % (name, n), pl, kind, form, tok, why))
            added[name] += 1
            n += 1
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
    head, rows = rows[0], [r for r in rows[1:] if r[0] == at]
    tips = {(r[1], r[4]): r for r in [x for x in [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")
                                                  if l.strip() and not l.startswith("#")][1:] if x[0] == "tip"]}
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
    bad = 0
    try:
        rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]
    except OSError as e:
        sys.stderr.write("%s\n" % e)
        sys.exit(2)
    oq = False
    for r in rows:
        name, body, want_c, want_d = r[0], r[1], r[2], r[3]
        counted, dropped, oq = match_line(body, oq if name.endswith("+cont") else False)
        got_c = " ".join("%s:%s" % c for c in counted) or "-"
        got_d = " ".join("%s:%s:%s" % d for d in dropped) or "-"
        ok = got_c == want_c and got_d == want_d
        bad |= not ok
        print("%s %s: counted %s; dropped %s" % ("PASS" if ok else "FAIL", name, got_c, got_d))
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
