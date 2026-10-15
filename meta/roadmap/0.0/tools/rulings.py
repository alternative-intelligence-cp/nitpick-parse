#!/usr/bin/env python3
"""Cycle 0.0 -- the shapes the compiler's rulings in landing 112's commit (D-353 … D-359) and its landing 114
(DEF-250) refuse or reserve, counted over `.npk` files the way `shapes.py` counts (comments and strings blanked),
so a plan can say which it writes. Added by cycle 0.0.2's plan.

    python3 -B rulings.py [--sites] <file>...

  a module-level binding, by kind    landing 114 (DEF-250): one with NO initialiser is `NITPICK-TYPE-055` at its
                                     declaration, as a plain one with an initialiser already is at the pin
                                     (D-211); a `fixed` one with an initialiser is the kind that stays
  `NULL`                             D-355: legal only for a `wild` pointer, by a landing of its own
  `comptime`                         D-353: a value parameter is RESERVED (landing 117); a `comptime func:` is
                                     compile-time only
  an impl declared away from both    the orphan rule (S-37): an `impl:<Type>:<Trait>` lives in the module of its
  its trait and its type             trait or its type; one whose file declares neither is the shape to read
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import blank  # noqa: E402

_DECL = re.compile(r"\s*(pub\s+)?(func|struct|enum|trait|impl|mod|error|use|extern|macro|unit|rule)\b")
_BINDING = re.compile(r"\s*(pub\s+)?(fixed\s+|const\s+)?([\w<>\[\]\-?]+(?:->)?)\s*:\s*\w+\s*(=|;)")


def scan(path):
    with open(path, "rb") as fh:
        text = blank(fh.read().decode("utf-8", errors="replace"))
    found = {}

    def hit(kind, n):
        found.setdefault(kind, []).append("%s:%d" % (path, n))

    depth = 0
    for n, line in enumerate(text.split("\n"), 1):
        if depth == 0 and not _DECL.match(line):
            m = _BINDING.match(line)
            if m:
                if m.group(4) == ";":
                    hit("a module-level binding with no initialiser", n)
                elif m.group(2):
                    hit("a module-level binding, %s, initialised" % m.group(2).strip(), n)
                else:
                    hit("a module-level binding, plain, initialised", n)
        depth += line.count("{") - line.count("}")
        for _ in re.finditer(r"\bNULL\b", line):
            hit("`NULL`", n)
        for _ in re.finditer(r"\bcomptime\b", line):
            hit("`comptime`", n)
    declared = set(re.findall(r"\b(?:struct|enum|trait):(\w+)", text))
    for m in re.finditer(r"\bimpl:(\w+):(\w+)", text):
        if m.group(1) not in declared and m.group(2) not in declared:
            hit("an impl whose file declares neither its type nor its trait", text[:m.start()].count("\n") + 1)
    return found


def main(argv):
    sites = "--sites" in argv
    files = [a for a in argv[1:] if a != "--sites"]
    total = {}
    for f in files:
        for kind, where in scan(f).items():
            total.setdefault(kind, []).extend(where)
    print("%d file(s) read" % len(files))
    for kind in sorted(total):
        print("  %s: %d%s" % (kind, len(total[kind]), ("  " + " ".join(total[kind])) if sites else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
