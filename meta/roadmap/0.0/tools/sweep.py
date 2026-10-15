#!/usr/bin/env python3
"""Cycle 0.0 -- the stale-claim sweep a subcycle's last block runs after its prose lands, and its positive control.

    python3 -B sweep.py run     "$REPO" <subcycle>      # every candidate the patterns find, with denominators
    python3 -B sweep.py control "$REPO" <subcycle>      # the transform's self-test, then every removed hunk's old
                                                        # text, matched by some pattern?

The patterns are `meta/roadmap/0.0/<subcycle>_tools/sweep_patterns.txt`, one per line, `<subject> | <regex>`; each is
matched case-insensitively over JOINED text -- a file's lines with their leading `//`, `#`, `>` and `|` markers and
their emphasis stripped, and joined by single spaces -- so a claim that a line break or emphasis splits is still one
string (`PLAYBOOK.md` §12). A sweep for a claim about truth or tense builds a CANDIDATE list, and reading is the check:
each candidate's verdict is the plan's, in its sweep table.

THE TRANSFORM IS A CLAIM ABOUT EVERY PATTERN IT SERVES (the plan verification of 2026-10-15, its finding 4: an
emphasis strip that deleted every `_` made every pattern holding one unmatchable, in silence). So:
  * emphasis is a backtick or a run of `*`, deleted wherever it stands, and an `_` ONLY where it opens and closes an
    emphasised span -- never inside an identifier, so `NPARSE_DUP_SCAN_MAX` and `tools/parse_check` are matched whole;
  * a pattern holding a part the transform makes unmatchable is REFUSED, by name, before anything is swept: a
    literal `*` or backtick (the transform deletes both), a line anchor `^` or `$` (joined text has one line, so
    each would match only at the file's ends), a newline (the joining removes every one), or a heading's marker, two
    or more `#` and a space (the transform strips it from every line it starts) -- a part that can never match, even
    an optional one, says its pattern was written against the file and not against the joined text;
  * `control` runs the transform's own self-test first -- one planted text and pattern per character class, each
    matched, and one pattern per refused kind, each refused -- and prints its count.

`run` reads every file `git ls-files` lists plus every untracked file the steps added (`--others --exclude-standard`),
but the cycle 0.0 plans, the patches, the `.npk` sources, `LICENSE`, and the research digests -- a file whose first
line is a digest's heading, `# <topic> — research digest` (the workbench research skill's §5): a digest is dated and
never edited, so every sentence in it is history as of its date. It prints, per pattern, `<subject>: <n>
candidate(s) in <m> file(s)`, then `<file>:<line>` for each, the line counted in the ORIGINAL file. The denominator
line comes first.

`control` then reads the patches' REMOVED lines, hunk by hunk, and reports the hunks whose old text no pattern
matches -- each is a kind of sentence the sweep cannot see, which the plan names (`PLAYBOOK.md` §12: a stale-claim
sweep's patterns get a positive control, the step's own hunks).
"""
import glob
import os
import re
import re._parser as sre_parse
import subprocess
import sys

MARKS = re.compile(r"^\s*(//+|#+|>+|\|)\s?")
EMPH = re.compile(r"`|\*+")
EMPH_UNDERSCORE = re.compile(r"(?<![A-Za-z0-9_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![A-Za-z0-9_])")
DIGEST = re.compile(r"^# .+ — research digest\s*$")


def strip(line):
    """One line as the patterns see it: its leading marker, its backticks and `*` runs, and its `_` emphasis gone."""
    s = MARKS.sub("", line)
    s = EMPH_UNDERSCORE.sub(r"\1", s)
    return EMPH.sub("", s).strip()


def unmatchable(rx):
    """Why the transform makes this pattern unable to match, or None."""
    found = []

    def walk(node):
        if isinstance(node, sre_parse.SubPattern):
            node = node.data
        if isinstance(node, (list, tuple)):
            if len(node) == 2 and isinstance(node[0], int) and hasattr(node[0], "name"):
                op, av = node
                name = op.name
                if name == "LITERAL" and av in (42, 96, 10):
                    found.append({42: "a literal `*`", 96: "a literal backtick", 10: "a newline"}[av])
                elif name == "AT" and av.name in ("AT_BEGINNING", "AT_END", "AT_BEGINNING_STRING", "AT_END_STRING"):
                    found.append("a line anchor")
                elif name == "IN":
                    for item in av:
                        if item[0].name == "LITERAL" and item[1] in (42, 96, 10):
                            found.append({42: "a literal `*`", 96: "a literal backtick", 10: "a newline"}[item[1]])
                else:
                    walk(av)
                return
            for x in node:
                walk(x)

    walk(sre_parse.parse(rx, re.I))
    if re.search(r"(?<!\\)##+ ", rx):
        found.append("a heading's marker")
    return ", ".join(sorted(set(found))) or None


def plan_dir(root):
    d = os.path.join(root, "meta", "roadmap", "0.0")
    return d if os.path.isdir(d) else os.path.join(root, "meta", "roadmap", "done", "0.0")


def patterns(root, sub):
    out = []
    with open(os.path.join(plan_dir(root), sub + "_tools", "sweep_patterns.txt"), encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            subj, _, rx = line.rstrip("\n").partition(" | ")
            why = unmatchable(rx.strip())
            if why:
                raise SystemExit("STOP: %s's pattern `%s` holds %s, which the transform removes -- it can never match"
                                 % (sub, subj.strip(), why))
            out.append((subj.strip(), re.compile(rx.strip(), re.I)))
    return out


def joined(lines):
    """The joined text and, for each character, the 1-based line it came from."""
    parts, where = [], []
    for n, line in enumerate(lines, 1):
        s = strip(line)
        if not s:
            continue
        if parts:
            parts.append(" "); where.append(n)
        parts.append(s); where.extend([n] * len(s))
    return "".join(parts), where


# The self-test: (what the class is, the planted lines, the pattern that must match them).
_PLANTED = [
    ("letters", ["plain words"], r"plain words"),
    ("digits and a hyphen", ["the 24-byte value"], r"\b24[- ]?bytes?\b"),
    ("an identifier's `_`", ["beyond `NPARSE_DUP_SCAN_MAX` (1024 pairs)"], r"NPARSE_DUP_SCAN_MAX \(1024"),
    ("a path's `/` and `_`", ["see tools/parse_check here"], r"tools/parse_check"),
    ("a call's `.` and parentheses", ["`string_bytes(t).len`"], r"string_bytes\(t\)\.len"),
    ("emphasis around words", ["**no** _stack_ *depth* guard"], r"no stack depth guard"),
    ("a claim across a line break", ["a claim that a line", "break splits"], r"line break splits"),
    ("a comment's marker", ["// held by the comment"], r"held by the comment"),
    ("a heading's marker", ["## Heading words"], r"Heading words"),
    ("a quotation's marker", ["> quoted words"], r"quoted words"),
    ("a table row's marker", ["| cell | next |"], r"cell \| next"),
]
_REFUSED = [r"uncontrolled\*\* fault", r"`code`", r"^starts here", r"ends here$", r"one\ntwo", r"## heading words"]


def selftest():
    good = sum(1 for _, lines, rx in _PLANTED if re.search(rx, joined(lines)[0], re.I))
    refused = sum(1 for rx in _REFUSED if unmatchable(rx))
    print("the transform: %d of %d planted patterns, one per character class, matched; %d of %d unmatchable "
          "patterns refused" % (good, len(_PLANTED), refused, len(_REFUSED)))
    return good == len(_PLANTED) and refused == len(_REFUSED)


def files(root):
    out = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split()
    out += subprocess.run(["git", "-C", root, "ls-files", "--others", "--exclude-standard"],
                          capture_output=True, text=True).stdout.split()
    skip = re.compile(r"(^|/)meta/roadmap/(done/)?0\.0/|\.patch$|\.npk$|^LICENSE$")
    return sorted(f for f in set(out) if not skip.search(f) and os.path.isfile(os.path.join(root, f)))


def run(root, sub):
    pats = patterns(root, sub)
    texts = {}
    for f in files(root):
        with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        if lines and DIGEST.match(lines[0]):
            continue
        texts[f] = joined(lines)
    fs = sorted(texts)
    print("denominator: %d file(s) -- every tracked or added file but the cycle 0.0 plans, patches, sources, LICENSE "
          "and the research digests" % len(fs))
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
    ok = selftest()
    pats = patterns(root, sub)
    tools = os.path.join(plan_dir(root), sub + "_tools")
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
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("run", "control"):
        print(__doc__)
        sys.exit(2)
    sys.exit((run if sys.argv[1] == "run" else control)(os.path.realpath(sys.argv[2]), sys.argv[3]))
