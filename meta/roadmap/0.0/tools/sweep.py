#!/usr/bin/env python3
"""Cycle 0.0 -- the stale-claim sweep a subcycle's last block runs after its prose lands, and its positive control.

    python3 -B sweep.py run     "$REPO" <subcycle>      # every candidate the patterns find, with denominators
    python3 -B sweep.py control "$REPO" <subcycle>      # every removed hunk's old text, matched by some pattern?

The patterns are `meta/roadmap/0.0/<subcycle>_tools/sweep_patterns.txt`, one per line, `<subject> | <regex>`; each is
matched case-insensitively over JOINED text -- a file's lines with their leading `//`, `#`, `>` and `|` markers and
emphasis (`*`, `_`, backticks) stripped and joined by single spaces -- so a claim that a line break or emphasis splits
is still one string (`PLAYBOOK.md` §12). A sweep for a claim about truth or tense builds a CANDIDATE list, and reading is
the check: each candidate's verdict is the plan's, in its sweep table.

`run` reads every file `git ls-files` lists plus every untracked file the steps added (`--others --exclude-standard`),
and prints, per pattern, `<subject>: <n> candidate(s) in <m> file(s)`, then `<file>:<line>` for each, the line
counted in the ORIGINAL file. The denominator line comes first.

`control` reads the patches' REMOVED lines, hunk by hunk, and reports the hunks whose old text no pattern matches --
each is a kind of sentence the sweep cannot see, which the plan names (`PLAYBOOK.md` §12: a stale-claim sweep's
patterns get a positive control, the step's own hunks).
"""
import glob
import os
import re
import subprocess
import sys

MARKS = re.compile(r"^\s*(//+|#+|>+|\|)\s?")
EMPH = re.compile(r"[*_`]")


def patterns(root, sub):
    out = []
    d = os.path.join(root, "meta", "roadmap", "0.0")
    d = d if os.path.isdir(d) else os.path.join(root, "meta", "roadmap", "done", "0.0")
    with open(os.path.join(d, sub + "_tools", "sweep_patterns.txt"), encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            subj, _, rx = line.rstrip("\n").partition(" | ")
            out.append((subj.strip(), re.compile(rx.strip(), re.I)))
    return out


def joined(lines):
    """The joined text and, for each character, the 1-based line it came from."""
    parts, where = [], []
    for n, line in enumerate(lines, 1):
        s = EMPH.sub("", MARKS.sub("", line)).strip()
        if not s:
            continue
        if parts:
            parts.append(" "); where.append(n)
        parts.append(s); where.extend([n] * len(s))
    return "".join(parts), where


def files(root):
    out = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split()
    out += subprocess.run(["git", "-C", root, "ls-files", "--others", "--exclude-standard"],
                          capture_output=True, text=True).stdout.split()
    skip = re.compile(r"(^|/)meta/roadmap/0\.0/|\.patch$|\.npk$|^LICENSE$")
    return sorted(f for f in set(out) if not skip.search(f) and os.path.isfile(os.path.join(root, f)))


def run(root, sub):
    pats = patterns(root, sub)
    fs = files(root)
    texts = {}
    for f in fs:
        with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
            texts[f] = joined(fh.read().split("\n"))
    print("denominator: %d file(s) -- every tracked or added file but the cycle 0.0 plans, patches, sources and LICENSE" % len(fs))
    for subj, rx in pats:
        hits = []
        for f in fs:
            t, where = texts[f]
            for m in rx.finditer(t):
                hits.append("%s:%d" % (f, where[m.start()]))
        nf = len({h.rsplit(":", 1)[0] for h in hits})
        print("%s: %d candidate(s) in %d file(s)" % (subj, len(hits), nf))
        for h in hits:
            print("  " + h)
    return 0


def control(root, sub):
    pats = patterns(root, sub)
    tools = os.path.join(root, "meta", "roadmap", "0.0", sub + "_tools")
    if not os.path.isdir(tools):
        tools = os.path.join(root, "meta", "roadmap", "done", "0.0", sub + "_tools")
    total = matched = 0
    misses = []
    for p in sorted(glob.glob(os.path.join(tools, "step*.patch"))):
        cur, hunk, removed = None, None, []

        def close():
            nonlocal total, matched
            if removed and cur and not re.search(r"\.(npk|patch)$", cur):
                total += 1
                t, _ = joined(removed)
                if any(rx.search(t) for _, rx in pats):
                    matched += 1
                else:
                    misses.append("%s %s %s" % (os.path.basename(p), cur, hunk))
        for line in open(p, encoding="utf-8"):
            if line.startswith("diff --git "):
                close(); removed = []; cur = None
            elif line.startswith("+++ b/"):
                cur = line[6:].strip()
            elif line.startswith("@@"):
                close(); removed = []; hunk = line.split("@@")[1].strip()
            elif line.startswith("-") and not line.startswith("---"):
                removed.append(line[1:].rstrip("\n"))
        close()
    print("hunks that remove prose: %d; matched by a pattern: %d; not matched: %d" % (total, matched, total - matched))
    for m in misses:
        print("  NOT MATCHED " + m)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("run", "control"):
        print(__doc__)
        sys.exit(2)
    sys.exit((run if sys.argv[1] == "run" else control)(os.path.realpath(sys.argv[2]), sys.argv[3]))
