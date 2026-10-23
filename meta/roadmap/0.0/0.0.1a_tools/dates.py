#!/usr/bin/env python3
"""0.0.1a -- every line this subcycle's two patches date or re-date, as step 2 leaves the tree: the libraries' seat's
ruling (a) of 2026-10-22 on cycle 0.0.0's 29 drafting-dated lines, and this subcycle's own dated notes.

    python3 -B dates.py <tree>

Printed, each as `<group> <file>:<n>: <text>`, the line found by a text it carries, cut at 150 characters:

  * `(note)` -- the 19 notes cycle 0.0.0's commits landed, each now opening with 2026-10-17, the day those commits
    reached `main`; a 0.0.0 note still opening with its drafting date, 2026-10-15 or 2026-10-16, prints as a `STALE`
    line, so the block shows it;
  * `(site)` -- the ten `meta/DECISIONS.md` sites, each its own line unchanged (its 2026-10-15 included), and the
    line beneath it, which must be this subcycle's note;
  * `(re-pin)` -- `PA-111`'s note on its reversal, `VERIFICATION.md` §2's note on landing 128, and the two probe
    headers that now call the re-pin to `c9baa9e` the libraries' first.

A date prints with `/` (2026/10/17) because the comparator masks an ISO date, which would hide a wrong one; the run's
own date, the one `../tools/apply.py` recorded in `.internal/w00/0.0.1a.date`, prints as `<the run's date>`, which no
Expect can know. A site whose text is missing prints NOT FOUND, and so does a missing date file: either is a DIFF.
"""
import os
import re
import sys

NOTE_FILES = ["meta/DECISIONS.md", "meta/OPEN_QUESTIONS.md", "meta/specs/DIAGNOSTIC_MODEL.md",
              "meta/specs/EVENT_MODEL.md", "meta/specs/PLUGIN_MODEL.md", "meta/specs/SAFETY.md",
              "meta/specs/SCAN_MODEL.md", "meta/specs/VALUE_MODEL.md", "meta/specs/VERIFICATION.md"]
SITES = [r"^> \*\*SUPERSEDED IN PART by PA-1(0[4-9]) .*\(2026-10-15\)", r"^\*\*2026-10-15, cycle 0\.0\.0"]
REPIN = [("meta/DECISIONS.md", r"cycle 0\.0\.1a:\)\* the re-pin at landing 118 was the first"),
         ("meta/specs/VERIFICATION.md", r"cycle 0\.0\.1a: from the compiler's landing 128"),
         ("tests/probe/probe06_trait_bound.npk", r"the libraries' first re-pin"),
         ("tests/probe/refused/probe08h_view_reseated.npk", r"the libraries' first re-pin")]


def main(argv):
    root = os.path.realpath(argv[1])
    stamp = os.path.join(root, ".internal", "w00", "0.0.1a.date")
    day = open(stamp, encoding="utf-8").read().strip() if os.path.isfile(stamp) else None
    print("the run's date: %s" % ("recorded in .internal/w00/0.0.1a.date" if day else
                                  "NOT FOUND -- no .internal/w00/0.0.1a.date"))

    def show(text):
        if day:
            text = text.replace(day, "<the run's date>")
        return re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", r"\1/\2/\3", text.strip())[:150]

    def lines(path):
        return open(os.path.join(root, path), encoding="utf-8").read().split("\n")

    notes = 0
    for path in NOTE_FILES:
        for n, line in enumerate(lines(path), 1):
            m = re.match(r"^\*\((2026-10-1[5-7]), cycle 0\.0\.0[,:\s—]", line)
            if m:
                notes += 1
                print("(%s) %s:%d: %s" % ("note" if m.group(1) == "2026-10-17" else "STALE", path, n, show(line)))
    print("(note) 0.0.0's notes found: %d" % notes)
    dec = lines("meta/DECISIONS.md")
    sites = 0
    for n, line in enumerate(dec, 1):
        if any(re.search(rx, line) for rx in SITES):
            sites += 1
            under = next((k for k in range(n, min(n + 30, len(dec))) if "cycle 0.0.1a:)* this" in dec[k]), None)
            print("(site) meta/DECISIONS.md:%d: %s" % (n, show(line)))
            print("(site)   beneath it, line %s: %s" % (under + 1 if under is not None else "NOT FOUND",
                                                       show(dec[under]) if under is not None else "no 0.0.1a note"))
    print("(site) decision sites found: %d" % sites)
    for path, rx in REPIN:
        hits = [(n, line) for n, line in enumerate(lines(path), 1) if re.search(rx, line)]
        if not hits:
            print("(re-pin) %s: NOT FOUND: %s" % (path, rx))
        for n, line in hits:
            print("(re-pin) %s:%d: %s" % (path, n, show(line)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
