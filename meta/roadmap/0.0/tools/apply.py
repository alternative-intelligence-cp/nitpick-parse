#!/usr/bin/env python3
"""Cycle 0.0 -- apply one subcycle step's patch, all-or-nothing, and say which of three states the tree was in.

    python3 -B apply.py "$REPO" <subcycle> <step>        e.g.  apply.py "$REPO" 0.0.0 2

The patch is `meta/roadmap/0.0/<subcycle>_tools/step<step>.patch` BESIDE THIS SCRIPT -- the plan's own, whatever tree
it is applied to -- a `git diff` of the design chain the plan was cut from, and the review surface: a worker may tighten a text, never change what it says, and amends THE PATCH, never
the tree by hand (the workbench `PLAYBOOK.md` §12).

A STEP IS A NUMBER, OR A NUMBER AND ONE LETTER for one part of that step: `step0c.patch` is step 0's part c, and a
step's parts come after it and before the next step, in their letters' order -- `step0c.patch`, `step0d.patch`,
`step0e.patch`, then `step1.patch` (cycle 0.0.3's step cut, which put the libraries' seat's three harness gaps in its
step 0 as parts, so that its steps 1 ... 3 keep the numbers the settled records cite).

THE DECISION NUMBERS ARE WRITTEN HERE, NOT IN THE PLAN. Every `@@PD-nnn@@` in a patch becomes this repository's
number for that proposed decision: `decisions.txt` beside this tool lists the accepted PDs in order after a `base`,
and PD at rank k (1-based) is `PA-<base + k>`. A placeholder with no line there is a STOP: the review declined it,
and the hunks that carry it must be re-cut first. The same substitution runs over every patch of every subcycle, so
a later patch's context holds the numbers an earlier one wrote.

  * the patch applies IN REVERSE  -> ALREADY: the step is in the tree; nothing written
  * the patch applies             -> APPLY: written and staged (`git apply --index`), every file of it
  * neither                       -> STOP: the tree is not the one the patch was cut from; nothing was written

`git apply` checks every hunk before it writes any, so a STOP writes nothing.

THE LABELS ARE CHECKED BEFORE ANY HUNK IS (the plan verification of 2026-10-15, its findings 1 and 5). A patch whose
added lines hold any of these is a STOP, by name, and nothing is written:
  * a BARE label, `PD-<n>` outside `@@...@@` -- the substitution never sees it, so it would land as a label no
    decision log defines, in a text the review makes immutable;
  * a number past the base written out, `PA-<n>` with n > base -- that number is the review's to give;
  * a placeholder CITED BEFORE THE STEP THAT DECLARES IT -- its `### @@PD-n@@` heading is added by a later patch,
    in plan order (every `<subcycle>_tools/step<k>.patch` beside this plan, subcycle by subcycle, step by step),
    so at this step's commit it would name a decision the log does not hold yet; or one that no step declares.

THE RUN'S DATE (from cycle 0.0.2, the libraries' seat's ruling of 2026-10-21 on 0.0.1's dates: a dated note says when
the tree began to say it, so it carries the day it lands, not the day the plan drafted it). Every `@@DATE@@` in a
patch becomes ONE date for the whole run of its subcycle: the day the run's first step that carries the placeholder
applied, which that step records in `.internal/w00/<subcycle>.date` of the tree it applies to. Every later step of the
run reads it there, so a run that crosses midnight, or spans days, writes one date everywhere: `nitpick-regex`'s
0.1.4 tool took each step's own day, and a run past midnight STOPPED at the first step whose context held an earlier
step's date (its `done/0.2/0.2.1_tools/apply.py` tells it). The file is the hand-off from one step's worker to the
next, kept between steps; the subcycle's last step removes it. A re-run reports ALREADY on any day while the file holds
the run's date. A file the patches touch must not hold `@@DATE@@` before they are applied -- a placeholder in a
patch's context would be replaced too, and the context would no longer match (the same file: `nitpick-regex` 0.2.0's
rehearsal STOPPED twice on that) -- and a later subcycle's patch must not hold an earlier run's dated line in its
context, since that date is known only when the earlier run lands. The patches' `index` lines are the raw chain's
blobs, every placeholder unsubstituted.
"""
import datetime
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = re.compile(r"@@(PD-\d+)@@")
DECLARES = re.compile(r"^\+### @@(PD-\d+)@@")
DATE_PLACEHOLDER = "@@DATE@@"


def date_file(root, sub):
    """The run's one date for a subcycle whose patches carry `@@DATE@@`: the file its first applying step writes."""
    return os.path.join(root, ".internal", "w00", sub + ".date")


def run_date(root, sub):
    """(the run's date, whether a step has recorded it): the recorded day, or today's when none has yet."""
    p = date_file(root, sub)
    if not os.path.isfile(p):
        return datetime.date.today().isoformat(), False
    with open(p, encoding="utf-8") as fh:
        day = fh.read().strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise SystemExit("STOP %s: .internal/w00/%s.date holds %r, not a date" % (sub, sub, day))
    return day, True


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


def base_number():
    for line in open(os.path.join(HERE, "decisions.txt"), encoding="utf-8"):
        m = re.fullmatch(r"base PA-(\d+)", line.strip())
        if m:
            return int(m.group(1))
    raise SystemExit("STOP: decisions.txt has no base line")


def plan_order():
    """Every step patch of the cycle beside this plan, in plan order: [(subcycle, step, path)], a step's parts
    after it (the module's docstring)."""
    out = []
    for d in sorted(glob.glob(os.path.join(HERE, "..", "0.0.*_tools"))):
        sub = os.path.basename(d)[:-len("_tools")]
        steps = []
        for p in glob.glob(os.path.join(d, "step*.patch")):
            m = re.search(r"step(\d+)([a-z]?)\.patch$", p)
            if m:
                steps.append(((int(m.group(1)), m.group(2)), p))
        out += [(sub, "%d%s" % k, p) for k, p in sorted(steps)]
    return out


def added(raw):
    return [line for line in raw.split("\n") if line.startswith("+") and not line.startswith("+++")]


def label_findings(sub, step, raw):
    """Each way this patch's added lines misuse a decision label (the module's docstring), or []."""
    bad, base = [], base_number()
    for line in added(raw):
        for m in re.finditer(r"\bPD-\d+\b", PLACEHOLDER.sub("", line)):
            bad.append("a bare %s in an added line -- a label is written @@%s@@" % (m.group(0), m.group(0)))
        for m in re.finditer(r"\bPA-(\d+)\b", line):
            if int(m.group(1)) > base:
                bad.append("%s written out in an added line -- a number past the base is the review's" % m.group(0))
    order = plan_order()
    steps = [(s, n) for s, n, _ in order]
    declared = {}
    for s, n, p in order:
        with open(p, encoding="utf-8", newline="") as fh:
            for line in added(fh.read()):
                m = DECLARES.match(line)
                if m:
                    declared.setdefault(m.group(1), (s, n))
    here = steps.index((sub, step)) if (sub, step) in steps else len(steps)
    for pd in sorted(set(PLACEHOLDER.findall("\n".join(added(raw))))):
        if pd not in declared:
            bad.append("%s is declared by no step of the cycle" % pd)
        elif steps.index(declared[pd]) > here:
            bad.append("%s is cited before the step that declares it, %s step%s" % ((pd,) + declared[pd]))
    return bad


def text_of(sub, step):
    # The patch is read from THIS PLAN's tools, beside this script, whatever tree it is applied to: a dry run in a
    # throwaway clone applies the plan's own text, not whatever the clone holds.
    path = os.path.normpath(os.path.join(HERE, "..", sub + "_tools", "step%s.patch" % step))
    if not os.path.isfile(path):
        raise SystemExit("STOP %s step%s: no %s_tools/step%s.patch beside this plan's tools" % (sub, step, sub, step))
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    bad = label_findings(sub, step, raw)
    if bad:
        raise SystemExit("STOP %s step%s: %s" % (sub, step, "; ".join(bad)))
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
    day, recorded = None, False
    if DATE_PLACEHOLDER in text:
        day, recorded = run_date(root, sub)
        text = text.replace(DATE_PLACEHOLDER, day)

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
    if day and not recorded:
        os.makedirs(os.path.dirname(date_file(root, sub)), exist_ok=True)
        with open(date_file(root, sub), "w", encoding="utf-8") as fh:
            fh.write(day + "\n")
    files = len(re.findall(r"^diff --git ", text, re.M))
    print("APPLY %s step%s: %d file(s)" % (sub, step, files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
