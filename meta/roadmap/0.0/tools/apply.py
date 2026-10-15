#!/usr/bin/env python3
"""Cycle 0.0 -- apply one subcycle step's patch, all-or-nothing, and say which of three states the tree was in.

    python3 -B apply.py "$REPO" <subcycle> <step>        e.g.  apply.py "$REPO" 0.0.0 2

The patch is `meta/roadmap/0.0/<subcycle>_tools/step<step>.patch` BESIDE THIS SCRIPT -- the plan's own, whatever tree
it is applied to -- a `git diff` of the design chain the plan was cut from, and the review surface: a worker may tighten a text, never change what it says, and amends THE PATCH, never
the tree by hand (the workbench `PLAYBOOK.md` §12).

THE DECISION NUMBERS ARE WRITTEN HERE, NOT IN THE PLAN. Every `@@PD-nnn@@` in a patch becomes this repository's
number for that proposed decision: `decisions.txt` beside this tool lists the accepted PDs in order after a `base`,
and PD at rank k (1-based) is `PA-<base + k>`. A placeholder with no line there is a STOP: the review declined it,
and the hunks that carry it must be re-cut first. The same substitution runs over every patch of every subcycle, so
a later patch's context holds the numbers an earlier one wrote.

  * the patch applies IN REVERSE  -> ALREADY: the step is in the tree; nothing written
  * the patch applies             -> APPLY: written and staged (`git apply --index`), every file of it
  * neither                       -> STOP: the tree is not the one the patch was cut from; nothing was written

`git apply` checks every hunk before it writes any, so a STOP writes nothing.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = re.compile(r"@@(PD-\d+)@@")


def numbers():
    base, order = None, []
    with open(os.path.join(HERE, "decisions.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("base "):
                m = re.fullmatch(r"base PA-(\d+)", line)
                if not m:
                    raise SystemExit("STOP: decisions.txt's base line is not `base PA-<n>`: %r" % line)
                base = int(m.group(1))
            elif re.fullmatch(r"PD-\d+", line):
                order.append(line)
            else:
                raise SystemExit("STOP: decisions.txt holds a line that is neither a PD nor the base: %r" % line)
    if base is None:
        raise SystemExit("STOP: decisions.txt has no base line")
    return {pd: "PA-%03d" % (base + k + 1) for k, pd in enumerate(order)}


def text_of(sub, step):
    # The patch is read from THIS PLAN's tools, beside this script, whatever tree it is applied to: a dry run in a
    # throwaway clone applies the plan's own text, not whatever the clone holds.
    path = os.path.normpath(os.path.join(HERE, "..", sub + "_tools", "step%s.patch" % step))
    if not os.path.isfile(path):
        raise SystemExit("STOP %s step%s: no %s_tools/step%s.patch beside this plan's tools" % (sub, step, sub, step))
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    table = numbers()
    missing = sorted(set(PLACEHOLDER.findall(raw)) - set(table))
    if missing:
        raise SystemExit("STOP %s step%s: no decision number for %s in decisions.txt" % (sub, step, ", ".join(missing)))
    return PLACEHOLDER.sub(lambda m: table[m.group(1)], raw)


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    root, sub, step = os.path.realpath(argv[1]), argv[2], argv[3]
    text = text_of(sub, step)

    def git(*args):
        return subprocess.run(["git", "-C", root, "apply", "--index", *args, "-"],
                              input=text, text=True, capture_output=True)

    if git("--reverse", "--check").returncode == 0:
        print("ALREADY %s step%s" % (sub, step))
        return 0
    r = git("--check")
    if r.returncode == 0:
        r = git()
    if r.returncode != 0:
        print("STOP %s step%s: %s" % (sub, step, " | ".join(r.stderr.strip().splitlines()[:6])))
        return 1
    files = len(re.findall(r"^diff --git ", text, re.M))
    print("APPLY %s step%s: %d file(s)" % (sub, step, files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
