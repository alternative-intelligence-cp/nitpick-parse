#!/usr/bin/env python3
"""Cycle 0.0 -- every pointer the patches' added lines write, checked against the tree the patches leave
(`PLAYBOOK.md` §12: "a pointer in an added line is checked against the documents as the patches leave them, rule
numbers too").

    python3 -B pointers.py <patched tree> <subcycle tools dir>

Reads the `+` lines of every `step*.patch` in the tools dir, and reports:
  * every specification RULE id they cite -- `C-2`, `E-16`, `S-5` ... (a letter and an unpadded number; the
    compiler's decisions are `D-` and three digits, and are not this repository's) -- with the file that DEFINES it
    (a `**Rule <id>` line in `meta/specs/`), or `UNDEFINED`;
  * every section they cite as `` `<FILE>.md` §<n> `` with the file it resolves to and whether that file has a
    heading `## <n>.`, or `NO SUCH SECTION`. A section of a document outside this repository (the compiler's, the
    workbench's) is listed as such, unresolved here and read by the plan's §1.
"""
import glob
import os
import re
import sys

RULE = re.compile(r"(?<![\w-])([A-Z]-\d{1,2})(?![\w-])")
SECTION = re.compile(r"`([A-Z_]+\.md)`\s+§(\d+)")
OUTSIDE = {"PLAYBOOK.md", "TYPE_REFERENCE.md", "MEMORY_REFERENCE.md", "TRAITS_REFERENCE.md", "CONTROL_REFERENCE.md",
           "BUILD_REFERENCE.md", "VERIFICATION_REFERENCE.md", "IO_REFERENCE.md", "MACRO_REFERENCE.md",
           "BUILTIN_REFERENCE.md", "LEXICAL_REFERENCE.md", "MODULE_REFERENCE.md", "TCB.md"}


def main(argv):
    tree, tools = argv[1], argv[2]
    added = []
    for p in sorted(glob.glob(os.path.join(tools, "step*.patch"))):
        cur = None
        for line in open(p, encoding="utf-8"):
            if line.startswith("+++ b/"):
                cur = line[6:].strip()
            elif line.startswith("+") and not line.startswith("+++") and cur and cur.endswith(".md"):
                added.append(line[1:])
    text = "".join(added)
    defined = {}
    for f in sorted(glob.glob(os.path.join(tree, "meta", "specs", "*.md"))):
        for m in re.finditer(r"\*\*Rule ([A-Z]-\d+)\b", open(f, encoding="utf-8").read()):
            defined.setdefault(m.group(1), os.path.basename(f))
    rules = sorted(set(RULE.findall(text)), key=lambda r: (r.split("-")[0], int(r.split("-")[1])))
    bad = [r for r in rules if r not in defined]
    print("§1.8 rules cited by the added lines: %d -- %s" % (len(rules), " ".join(
        "%s(%s)" % (r, defined.get(r, "UNDEFINED")) for r in rules)))
    print("§1.8 undefined: %s" % (" ".join(bad) or "none"))
    secs = sorted(set(SECTION.findall(text)))
    out, missing = [], []
    for f, n in secs:
        if f in OUTSIDE:
            out.append("%s §%s (outside)" % (f, n))
            continue
        hits = glob.glob(os.path.join(tree, "meta", "specs", f)) + glob.glob(os.path.join(tree, f))
        ok = any(re.search(r"^## %s\." % n, open(h, encoding="utf-8").read(), re.M) for h in hits)
        out.append("%s §%s (%s)" % (f, n, "ok" if ok else "NO SUCH SECTION"))
        if not ok:
            missing.append("%s §%s" % (f, n))
    print("§1.8 sections cited: %d -- %s" % (len(secs), "; ".join(out)))
    print("§1.8 sections that do not resolve: %s" % (" ".join(missing) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
