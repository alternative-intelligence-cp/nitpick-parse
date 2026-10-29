#!/usr/bin/env python3
"""0.0.3 -- the harness's own checks, each broken alone in a copy of the tree, and what the runner says.

    python3 -B mutants.py <tree> [--staged] [<name> ...]

Every row of `mutants.tsv` beside this script, `name<TAB>file<TAB>old<TAB>new` (`\\n` a newline, `\\t` a tab in a
text), is one edit; the rows sharing a name are one mutant. For the unchanged tree and then each mutant in the
table's order, the tree's COMMITTED `HEAD` is copied (`git archive`) into `$A/mut/<name>/`, each edit made
EXACTLY ONCE -- any other count is a STOP, printed, and that mutant is not run -- and `harness/run.py` is run in
the copy with `$NPKC` and `$NPKRT` from the environment. It prints one line per mutant: `<name>: exit <n> --` and
the run's first failing line (a `FAIL` line, else a `failed:` line, else its `CANNOT PROCEED` line), cut at 200
characters, or its summary when nothing failed. Three run at a time; the copies are removed at the end. Each
mutant breaks ONE facet of one check, so the line names the check that saw it (`0.0.3.md` §5).

NAMES run those mutants alone, in the table's order, and not the unchanged tree; a name the table does not hold is a
STOP, exit 2, before anything is copied. `--staged` copies the tree's INDEX, what its next `git commit` commits
(`git checkout-index`), in place of its `HEAD`: so a block can run a harness gap's mutants over `HEAD`, the tree
before the gap's patch, and over the index with the patch staged -- the hole, and the fix refusing it, before the
fix is committed (`0.0.3.md` §3, step 0).
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def table():
    order, rows = [], {}
    with open(os.path.join(HERE, "mutants.tsv"), encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            name, f, old, new = line.rstrip("\n").split("\t")
            un = lambda t: t.replace("\\n", "\n").replace("\\t", "\t")
            if name not in rows:
                order.append(name)
                rows[name] = []
            rows[name].append((f, un(old), un(new)))
    return order, rows


def one(tree, base, staged, name, edits):
    d = os.path.join(base, name)
    os.makedirs(d)
    if staged:
        subprocess.run(["git", "-C", tree, "checkout-index", "--all", "--prefix=" + d + os.sep], check=True)
    else:
        arc = subprocess.run(["git", "-C", tree, "archive", "HEAD"], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", d], input=arc, check=True)
    for f, old, new in edits:
        p = os.path.join(d, f)
        s = open(p, encoding="utf-8").read()
        if s.count(old) != 1:
            return f"{name}: STOP -- the text to replace occurs {s.count(old)} times in {f}"
        open(p, "w", encoding="utf-8").write(s.replace(old, new))
    r = subprocess.run([sys.executable, "-B", os.path.join(d, "harness", "run.py")], cwd=d,
                       capture_output=True, text=True)
    lines = (r.stdout + r.stderr).splitlines()
    key = (next((x for x in lines if x.startswith("FAIL")), None)
           or next((x.strip() for x in lines if x.startswith("  failed:")), None)
           or next((x for x in lines if "CANNOT PROCEED" in x), None)
           or (lines[-1] if lines else "no output"))
    return f"{name}: exit {r.returncode} -- {key[:200]}"


def main(argv):
    staged = "--staged" in argv[2:]
    tree, names = os.path.realpath(argv[1]), [a for a in argv[2:] if a != "--staged"]
    base = os.path.join(os.environ["A"], "mut")
    order, rows = table()
    unknown = [n for n in names if n not in rows]
    if unknown:
        print("STOP -- mutants.tsv holds no mutant named " + ", ".join(unknown))
        return 2
    shutil.rmtree(base, ignore_errors=True)
    jobs = ([(n, rows[n]) for n in order if n in names] if names
            else [("unchanged", [])] + [(n, rows[n]) for n in order])
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        results = list(ex.map(lambda j: one(tree, base, staged, *j), jobs))
    for line in results:
        print(line)
    shutil.rmtree(base, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
