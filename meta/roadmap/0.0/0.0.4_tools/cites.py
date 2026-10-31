#!/usr/bin/env python3
r"""cites.py -- the citation census of the text 0.0.4's merge freezes (T18fix, (CC); management_10's ruling of
2026-10-31 07:54 and nitpick-libs_35's C1, C2, E2 and N1), its four gaps fixed in parse's next text round (T19, (CP):
T18v2's finding 1, as nitpick-libs_35 disposed of it at 10:00:52). A census, not a completeness check: the grep finds
the citation forms below and nothing else, and every hit is then read by hand against its cited line (`cites.tsv`).

    python3 -B cites.py run    <base> <tip> [plans]                 # every hit, its place and form; the excluded apart
    python3 -B cites.py record <base> <tip> <cites.tsv> <at> [plans] # the hits against the record's rows marked <at>
    python3 -B cites.py plants <cites_plants.tsv>                   # the planted twins, each through the census's reader

WHAT IT READS: `git diff -U0 <base> <tip>` of every `meta/roadmap/0.0/0.0.4_tools/step*.patch`, inside this
repository (`git -C`, the repository this file sits in), and every line that diff adds after its first hunk header.
Each hit's site is the patch and its line at <tip>. Its PLACE (nitpick-libs_35's C1): PATCH-ADDED where the patch line
begins `+` and is not a header, the text the merge freezes, a new claim; CONTEXT for every other patch line -- context
(` `), a hunk line (`@@`), a removed line (`-`) or a file header -- existing tree text, re-shown because a hunk moved.
A patch line's HEADER is read from the whole patch at <tip>: a `diff --git` line and every line after it up to its
first `@@` (`index`, a mode line, `--- a/...` and `+++ b/...`). A text line the patch adds or removes that begins
`++ `, `-- `, `+++ ` or `--- ` is no header, and is read as what it is.

THE PLANS (`plans`; T19's (CC2), management_10's ruling of 07:54, its last lines, and nitpick-libs_35's of 10:07): the
lines `git diff -U0 <base> <tip>` adds to `meta/roadmap/0.0/0.0.4.md` and to `0.0.5.md`, each file its own region,
each hit's site the file and its line at <tip>. Its PLACE is read from the whole file at <tip>: PROSE, TABLE (a line
beginning `|`), COMMENT (a fence's own comment, the plan's words: a `bash` line beginning `#`, a `nitpick` line's text
from `//`) or FENCE (the rest of a fenced block). Over the plans the forms are wider (EXTENSION below) and X4 joins.

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
EXTENSION, over the plans only (the patches' census is T18fix's, its forms as above):
  rule      parse's other rule forms too, `C-` `E-` `F-` `P-` `R-` `V-` (SCAN_MODEL, EVENT_MODEL, DIAGNOSTIC_MODEL,
            VERIFICATION, FORMATS, TESTING), and a rule's letter suffix (`BUILD.md` B-2a, `VERIFICATION.md` P-1a)
  code      a compiler code named bare as well (`RESOLVE-010`): a capital word of four letters or more, `-`, 3 digits
  finding   \bfindings? [0-9]+\b                 -- a report's finding
  cycle     \bcycles? [0-9]+\.[0-9]+(\.[0-9]+)?\b  -- a cycle cited by its number
  pointer   a line of a file, `<file>.<npk|py|patch|tsv|sh|toml|txt>:<n>`, or `:<n>` alone
THE EXCLUSIONS, each with its reason; `plants` runs a twin of each branch, and a twin where its reason stops:
  X1  a compiler diagnostic, named as the output it is: its code, always; and the quotation that follows the code,
      `("...")` or `"..."`, opening within 40 characters with no `(` or `"` between, only where it is THAT code's
      message: every part of its quoted words, cut at an elision (`…`), is in a message 0.0.4.md's record prints for
      that code at <tip> (a line `NITPICK-X-n <file>:<line>:<col>: <message>`, §1's items 11 and 12, re-run IDENTICAL
      by T18v). Each part of a quotation that runs on to the next line is read on its own line. A quotation that is
      not the code's message -- the plan's own words, another code's message -- keeps every citation in it, and a
      citation the plan writes itself, outside a quotation, is counted (nitpick-libs_35's N1). A code named bare
      (`RESOLVE-010`, the plans' extension) is read as `NITPICK-` and its name for its messages.
  X2  a document named in a patch's file header (above): a path, not a citation.
  X3  a document followed by a rule, open question or section of its own (`BUILD.md` B-16, `PLAYBOOK.md` §10): one
      citation, counted once, by the rule's form. OWN below names each rule form's documents; a section belongs to
      any document. A document followed by another document's rule (`BUILD.md` S-6) is counted, and so is the rule.
  X4  over the plans, a fenced block's lines but its comments: a `text` block (or one with no language) is a tool's
      or the compiler's output, verbatim or an Expect, and a `bash` command or `nitpick` code is the plan's command or
      program, none a claim of the plan's; every token on them is dropped. A comment is the plan's prose, and is
      counted; so is every line of a fence in any other language. A `bash` comment is a line beginning `#`: a `#`
      later on a command's line is read with the command, since it may stand in a quotation or a pattern
      (`grep -o '^### PA-[0-9]*'`); a `nitpick` comment is the line's text from its first `//`.
  PLANTS: a group whose first name begins `plans-` is a plan's lines, read whole by `regions` and through the plans'
      reader (`scan` with the regions, the extension's forms); every other group is a patch's lines, as above.
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
PLANS = ("meta/roadmap/0.0/0.0.4.md", "meta/roadmap/0.0/0.0.5.md")
PREFIXES2 = PREFIXES + ("C", "E", "F", "P", "R", "V")
RULE2 = r"(?:%s)-[0-9]{1,4}[a-z]?" % "|".join(PREFIXES2)
CODE2 = re.compile(r"\b(?:NITPICK-[A-Z]+-[0-9]+|[A-Z]{4,}-[0-9]{3})\b", re.I)
FORMS2 = [("rule", re.compile(r"\b%s\b" % RULE2, re.I))] + FORMS[1:4] + [("code", CODE2)] + FORMS[5:] + [
    ("finding", re.compile(r"\bfindings? [0-9]+\b", re.I)),
    ("cycle", re.compile(r"\bcycles? [0-9]+\.[0-9]+(?:\.[0-9]+)?\b", re.I)),
    ("pointer", re.compile(r"\b[\w./-]+\.(?:npk|py|patch|tsv|sh|toml|txt)\b`?:[0-9]+|(?<![\w.:`-])`?:[0-9]{2,5}\b")),
]
FOLLOWED2 = re.compile(r"`?(?:'s)?\s*(?:(§)|(%s)-[0-9]|(O-N)[0-9])" % "|".join(PREFIXES2), re.I)
OWN.update({"C": ("SCAN_MODEL.md",), "E": ("EVENT_MODEL.md",), "F": ("DIAGNOSTIC_MODEL.md",),
            "P": ("VERIFICATION.md",), "R": ("FORMATS.md",), "V": ("TESTING.md",)})
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
    key = code.upper() if code.upper().startswith("NITPICK-") else "NITPICK-" + code.upper()  # a code named bare
    return bool(parts) and all(any(p in m for m in msgs.get(key, ())) for p in parts)


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


def regions(lines):
    """Each line of a plan, by number: (PLACE, kind, the column X4 drops it to), read from its fences."""
    out, lang = {}, None
    for i, l in enumerate(lines, 1):
        s = l.lstrip()
        if s.startswith("```"):
            out[i] = ("FENCE", "edge", len(l))
            lang = (s[3:].strip().lower() or "text") if lang is None else None
        elif lang is None:
            out[i] = ("TABLE" if s.startswith("|") else "PROSE", "prose", 0)
        elif lang == "text":
            out[i] = ("FENCE", "output", len(l))
        elif lang in ("bash", "sh"):
            out[i] = ("COMMENT", "bash", 0) if s.startswith("#") else ("FENCE", "command", len(l))
        elif lang == "nitpick":
            c = l.find("//")
            out[i] = ("COMMENT", "nitpick", c) if c >= 0 else ("FENCE", "code", len(l))
        else:
            out[i] = ("FENCE", lang, 0)
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


def match_line(body, run_on, header, msgs, fence=0, plans=False):
    """Every form's hits on one line: (counted, dropped, run_on). A dropped hit carries its exclusion. `run_on` is the
    quotation a code's line left open, (code, closer), or None; `fence` the column before which X4 drops every token;
    `plans` the plans' forms."""
    forms, code_rx, followed = (FORMS2, CODE2, FOLLOWED2) if plans else (FORMS, CODE, FOLLOWED)
    spans = []                                   # X1's spans: a diagnostic's code, and its quoted message
    if run_on:                                   # a quotation run on from the line before
        code, closer = run_on
        close = body.find(closer)
        end = len(body) if close < 0 else close + len(closer)
        if is_message(code, body[:len(body) if close < 0 else close], msgs):
            spans.append((0, end))
        run_on = (code, closer) if close < 0 else None
    for m in code_rx.finditer(body):
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
    for form, rx in forms:
        for m in rx.finditer(body):
            tok = m.group(0).rstrip(".")
            f = followed.match(body, m.end()) if form == "document" else None
            if m.start() < fence:
                dropped.append((form, tok, "X4"))
            elif any(a <= m.start() < b for a, b in spans):
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


def scan(entries, heads, msgs, regs=None):
    """Each read line's (n, body, place, kind, counted, dropped), a quotation's run-on reset at every hunk. `regs`, a
    plan's regions, reads the lines as a plan's; without it they are a patch's."""
    out, run_on = [], None
    for n, body, first in entries:
        if first:
            run_on = None
        if regs is None:
            pl, kind = place(body, n in heads)
            counted, dropped, run_on = match_line(body, run_on, n in heads, msgs)
        else:
            pl, kind, fence = regs.get(n, ("PROSE", "prose", 0))
            counted, dropped, run_on = match_line(body, run_on, False, msgs, fence, True)
        out.append((n, body, pl, kind, counted, dropped))
    return out


def git(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr)
        sys.exit(2)
    return r.stdout


def census(base, tip, plans=False):
    files = PLANS if plans else sorted(f for f in git("ls-tree", "--name-only", tip, "meta/roadmap/0.0/0.0.4_tools/")
                                       .split() if re.search(r"/step[^/]*\.patch$", f))
    if not files:
        sys.stderr.write("no step*.patch at %s\n" % tip)
        sys.exit(2)
    msgs = messages(git("show", "%s:%s" % (tip, PLAN)))
    hits, drops, added = [], [], {}
    for f in files:
        name = f.rsplit("/", 1)[1]
        whole = git("show", "%s:%s" % (tip, f)).split("\n")
        heads, regs = (set(), regions(whole)) if plans else (headers(whole), None)
        lines = scan(read_diff(git("diff", "-U0", base, tip, "--", f)), heads, msgs, regs)
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
        if pl in ("PATCH-ADDED", "PROSE", "TABLE", "COMMENT"):
            c["PATCH-ADDED"][0].add(site)
            c["PATCH-ADDED"][1] += 1
    return out


def report(base, tip, plans=False):
    hits, drops, added = census(base, tip, plans)
    print("cites.py run %s %s%s: %d added line(s) read in %d %s" % (base, tip, " plans" if plans else "",
                                                                  sum(added.values()), len(added),
                                                                  "plan(s)" if plans else "patch(es)"))
    c = counts(hits)
    tl = th = pl = ph = 0
    for name in sorted(added):
        x = c.get(name, {"lines": set(), "hits": 0, "PATCH-ADDED": [set(), 0]})
        print("  %-14s %3d added line(s); %3d line(s), %3d hit(s); %s %3d line(s), %3d hit(s)"
              % (name, added[name], len(x["lines"]), x["hits"], "PATCH-ADDED",
                 len(x["PATCH-ADDED"][0]), x["PATCH-ADDED"][1]) if not plans else
              "  %-14s %3d added line(s); %3d line(s), %3d hit(s)" % (name, added[name], len(x["lines"]), x["hits"]))
        tl += len(x["lines"]); th += x["hits"]; pl += len(x["PATCH-ADDED"][0]); ph += x["PATCH-ADDED"][1]
    print("  %-14s %3d line(s), %3d hit(s); %s %3d line(s), %3d hit(s)" % (
        "all", tl, th, "PATCH-ADDED", pl, ph) if not plans else "  %-14s %3d line(s), %3d hit(s)" % ("all", tl, th))
    by = {}
    for h in hits:
        by[h[3]] = by.get(h[3], 0) + 1
    print("  by form: " + ", ".join("%s %d" % (f, by.get(f, 0)) for f, _ in (FORMS2 if plans else FORMS)))
    if plans:
        for name in sorted(added):
            pl = {}
            for h in hits:
                if h[0].split(":")[0] == name:
                    pl[h[1]] = pl.get(h[1], 0) + 1
            dr = {}
            for d in drops:
                if d[0].split(":")[0] == name:
                    dr[d[5]] = dr.get(d[5], 0) + 1
            print("  %-14s by place: %s; dropped: %s" % (name, ", ".join("%s %d" % (k, pl.get(k, 0)) for k in (
                "PROSE", "TABLE", "COMMENT", "FENCE")), ", ".join("%s %d" % (k, dr.get(k, 0)) for k in (
                "X1", "X3", "X4"))))
    for h in hits:
        print("HIT\t%s\t%s\t%s\t%s\t%s" % h)
    for d in drops:
        print("DROPPED\t%s\t%s\t%s\t%s\t%s\t%s" % d)
    return hits


def record(base, tip, path, at, plans=False):
    hits, _d, added = census(base, tip, plans)
    try:
        rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")
                if l.strip() and not l.startswith("#")]
    except OSError as e:
        sys.stderr.write("%s\n" % e)
        sys.exit(2)
    head, every = rows[0], rows[1:]
    rows = [r for r in every if r[0] == at and len(r) > 1 and r[1].split(":")[0] in added]  # this scope's rows
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
        if g[0][0].startswith("plans-"):        # a plan's lines, read whole: its regions, the plans' forms
            read = {x[0]: x for x in scan(read_diff(diff), set(), msgs, regions(bodies))}
        else:
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
    if a[:1] == ["run"] and (len(a) == 3 or len(a) == 4 and a[3] == "plans"):
        report(a[1], a[2], len(a) == 4)
        sys.exit(0)
    if a[:1] == ["record"] and (len(a) == 5 or len(a) == 6 and a[5] == "plans"):
        sys.exit(record(a[1], a[2], a[3], a[4], len(a) == 6))
    if a[:1] == ["plants"] and len(a) == 2:
        sys.exit(plants(a[1]))
    sys.stderr.write(__doc__)
    sys.exit(2)
