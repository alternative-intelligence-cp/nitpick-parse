#!/usr/bin/env python3
"""0.0.2 -- the twelve items of cycle 0.0.1's REPORT and of its work verifier, as the libraries' seat ruled them on
2026-10-21: each site's line as step 4 leaves the tree. Block 4 prints them, so the block shows every line the
step's patch changes, and the run's date wherever steps 1, 3 and 4 wrote it.

    python3 -B items.py <tree>

Each line is `(<item>) <file>:<n>: <text>`, the site found by a text the new line carries, cut at 150 characters.
A date prints with `/` (2026/10/21) because the comparator masks an ISO date, which would hide a wrong one; the
run's own date -- the one `../tools/apply.py` recorded in `.internal/w00/0.0.2.date` -- prints as `<the run's
date>`, which no Expect can know. A site whose text is missing prints NOT FOUND, and so does a missing date file:
either is a DIFF. Item (9) is the workflow's last step, read by YAML; item (12) has no site in the tree.
"""
import os
import re
import sys

import yaml

SITES = [
    ("1", "src/emit/emit.npk", r"built from cycle 0\.5, 0\.6, 0\.7, 0\.8\."),
    ("2", "meta/specs/BUILD.md", r"checks the layering against B-17's table"),
    ("2", "meta/specs/BUILD.md", r"this rule named B-17's drawing"),
    ("3", "nitpick.toml", r"Corrected \S+, cycle 0\.0\.1 --"),
    ("3", "nitpick.toml", r"20\.1\.8 since cycle 0\.0\.1, \S+ --"),
    ("3", "meta/specs/BUILD.md", r"^\*\(\S+, cycle 0\.0\.1, PA-\d+: until this subcycle"),
    ("3", "harness/README.md", r"^\*\(\S+, cycle 0\.0\.1:\)\*"),
    ("3", "meta/specs/FORMATS.md", r"^\*\(\S+, cycle 0\.0\.1, PA-\d+: this rule named"),
    ("3", "meta/roadmap/ROADMAP.md", r"^\*\(\S+, cycle 0\.0\.1 — the research gate"),
    ("3", "meta/DECISIONS.md", r"this marker landed on"),
    ("3", "meta/DECISIONS.md", r"this decision landed on"),
    ("3", "harness/README.md", r"^\*\(\S+, cycle 0\.0\.2: the stub is replaced"),
    ("3", "meta/DECISIONS.md", r"^\*\*\S+, cycle 0\.0\.2\.\*\*"),
    ("3", "meta/specs/BUILD.md", r"^\*\((Corrected|Re-read) \S+, cycle 0\.0\.2"),
    ("3", "meta/research/CURRENCY.md", r"^\| Python"),
    ("4", ".github/workflows/ci.yml", r"^# EVERY INPUT BUT THE RUNNER'S IMAGE IS PINNED"),
    ("4", ".github/workflows/ci.yml", r"^# Each action is pinned by the full commit sha"),
    ("4", ".github/workflows/ci.yml", r"^\s+uses: "),
    ("4", "meta/research/CURRENCY.md", r"^\| GitHub's `actions/checkout`"),
    ("10", ".github/workflows/ci.yml", r"^# `runs-on: ubuntu-24.04`, under which GitHub rolls"),
    ("10", ".github/workflows/ci.yml", r"^\s+# A release's label, not `ubuntu-latest`"),
    ("10", "meta/research/CURRENCY.md", r"^\| GitHub Actions' runner image"),
    ("5", "meta/research/CURRENCY.md", r"^\| UTF-8"),
    ("5", "meta/roadmap/0.0/0.0.1.md", r"cycle 0\.0\.2, for the libraries' seat's review of this record"),
    ("6", "CLAUDE.md", r"the pin `c9baa9e` a local named `stack`"),
    ("6", "meta/specs/BUILD.md", r"^\| `stack` \|"),
    ("6", "meta/roadmap/0.0/0.0.0.md", r"cycle 0\.0\.2:\)\* not at `c9baa9e`"),
    ("7", "CLAUDE.md", r"which cost `nitpick-regex`'s cycle 0\.0\.0"),
    ("8", ".github/workflows/ci.yml", r"^# WHAT A GREEN RUN PROVES SINCE CYCLE 0\.0\.2"),
    ("8", ".github/workflows/ci.yml", r"^\s+# Keyed on the compiler's commit and the LLVM release\. A hit rebuilds nothing"),
    ("11", "meta/roadmap/0.0/0.0.1.md", r"Step 5's entry counts one"),
]


def main(argv):
    root = os.path.realpath(argv[1])
    stamp = os.path.join(root, ".internal", "w00", "0.0.2.date")
    day = open(stamp, encoding="utf-8").read().strip() if os.path.isfile(stamp) else None
    print("the run's date: %s" % ("recorded in .internal/w00/0.0.2.date" if day else "NOT FOUND -- no .internal/w00/0.0.2.date"))

    def show(text):
        if day:
            text = text.replace(day, "<the run's date>")
        return re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", r"\1/\2/\3", text.strip())[:150]

    for item, path, rx in SITES:
        lines = open(os.path.join(root, path), encoding="utf-8").read().split("\n")
        hits = [(n, line) for n, line in enumerate(lines, 1) if re.search(rx, line)]
        if not hits:
            print("(%s) %s: NOT FOUND: %s" % (item, path, rx))
        for n, line in hits:
            print("(%s) %s:%d: %s" % (item, path, n, show(line)))
    steps = yaml.safe_load(open(os.path.join(root, ".github", "workflows", "ci.yml"), encoding="utf-8"))["jobs"]["build"]["steps"]
    print("(9) the workflow's last step: %s, %d of %d" % (steps[-1].get("name"), len(steps), len(steps)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
