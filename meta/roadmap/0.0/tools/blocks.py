#!/usr/bin/env python3
"""Cycle 0.0 -- run a subcycle plan's command blocks, and COMPARE each one's output with the plan's expected output.
The workbench `PLAYBOOK.md` §12: "the durable form of 'quote a command's whole output' is a COMPARATOR" -- care drops
lines; this does not. Modelled on `nitpick-regex`'s `meta/roadmap/0.2/0.2.4_tools/blocks.py`.

    python3 -B blocks.py list    "$REPO" <subcycle>               # the blocks, in order
    python3 -B blocks.py run     "$REPO" <subcycle> <id> [...]    # run blocks, save outputs
    python3 -B blocks.py compare "$REPO" <subcycle> <id> [...]    # diff saved outputs vs Expect

A BLOCK is a fenced `bash` block in `meta/roadmap/0.0/<subcycle>.md` whose first line is `# block <id>`; it is run by a
fresh `bash -c` with only `REPO=<the repository>` before it -- the worker's situation exactly, where no variable or
function survives from one call to the next, and where `grep` is GNU grep. Its output, stdout and stderr together,
goes to `$REPO/.internal/w00/blocks/<subcycle>-<id>.out`.

Its EXPECTED output is the fenced `text` block whose first line is `# expect <id>`. The comparison masks what
legitimately varies from run to run -- a run's seconds (`in 91.2 s`), the machine's free memory (`available GiB:`),
a calendar date, and `check_refs`'s file counts, which every later plan of the cycle moves -- and nothing else; a line the plan writes as `# (any)` matches any one line. It prints `SAME <id>`
or the lines that differ, and exits 1 if any block differs.
"""
import os
import re
import subprocess
import sys

FENCE = re.compile(r"^```(bash|text)\n(.*?)^```", re.S | re.M)
_MASKS = [
    (re.compile(r"\bin \d+(\.\d+)? s\b"), "in <s> s"),
    (re.compile(r"available GiB: \d+"), "available GiB: <n>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<date>"),
    # check_refs's denominators count every tracked file, this cycle's later plans and tools among them, so they
    # move with every subcycle the pass adds; its verdict -- clean, or each finding -- is what a block compares.
    (re.compile(r"\(\d+ md files via git ls-files; leak scan \d+ text of \d+ tracked\)"),
     "(<n> md files via git ls-files; leak scan <n> text of <n> tracked)"),
]


def plan_dir(root):
    """The cycle's folder, or its archive once cycle 0.0.5's last block has moved it to `done/0.0/`."""
    d = os.path.join(root, "meta", "roadmap", "0.0")
    return d if os.path.isdir(d) else os.path.join(root, "meta", "roadmap", "done", "0.0")


def blocks(root, sub):
    with open(os.path.join(plan_dir(root), sub + ".md"), encoding="utf-8") as fh:
        text = fh.read()
    runs, expects, order = {}, {}, []
    for m in FENCE.finditer(text):
        kind, body = m.group(1), m.group(2)
        first = body.split("\n", 1)[0].strip()
        if kind == "bash" and first.startswith("# block "):
            bid = first.split()[2]
            runs[bid] = body
            order.append(bid)
        elif kind == "text" and first.startswith("# expect "):
            expects[first.split()[2]] = body.split("\n", 1)[1] if "\n" in body else ""
    return order, runs, expects


def mask(line):
    for pat, rep in _MASKS:
        line = pat.sub(rep, line)
    return line.rstrip()


def compare_one(got, want):
    g = [mask(x) for x in got.rstrip("\n").split("\n")] if got.strip() else []
    w = [mask(x) for x in want.rstrip("\n").split("\n")] if want.strip() else []
    diffs = []
    for i in range(max(len(g), len(w))):
        a = g[i] if i < len(g) else "<missing>"
        b = w[i] if i < len(w) else "<missing>"
        if b.strip() == "# (any)" and a != "<missing>":
            continue
        if a != b:
            diffs.append("    line %d: got  %s\n    line %d: want %s" % (i + 1, a, i + 1, b))
    return diffs


def main(argv):
    if len(argv) < 4 or argv[1] not in ("list", "run", "compare"):
        print(__doc__)
        return 2
    cmd, root, sub = argv[1], os.path.realpath(argv[2]), argv[3]
    order, runs, expects = blocks(root, sub)
    ids = argv[4:] or order
    outdir = os.path.join(root, ".internal", "w00", "blocks")
    os.makedirs(outdir, exist_ok=True)
    if cmd == "list":
        for b in order:
            print("%-6s expect=%s" % (b, "yes" if b in expects else "NO"))
        return 0
    bad = 0
    for b in ids:
        if b not in runs:
            print("NO BLOCK %s" % b)
            bad += 1
            continue
        path = os.path.join(outdir, "%s-%s.out" % (sub, b))
        if cmd == "run":
            env = {k: v for k, v in os.environ.items() if not k.startswith("BASH_FUNC_")}
            r = subprocess.run(["bash", "-c", "REPO=%s\n" % repr(root) + runs[b]], capture_output=True,
                               text=True, env=env)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(r.stdout + r.stderr)
            print("RAN  %s: bash exit %d, %d lines" % (b, r.returncode, len((r.stdout + r.stderr).splitlines())))
        else:
            if b not in expects:
                print("NO EXPECT %s" % b)
                bad += 1
                continue
            got = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            d = compare_one(got, expects[b])
            if d:
                bad += 1
                print("DIFF %s" % b)
                print("\n".join(d))
            else:
                print("SAME %s" % b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
