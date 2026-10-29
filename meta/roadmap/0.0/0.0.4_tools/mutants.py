#!/usr/bin/env python3
"""0.0.4 -- the harness's checks and `src/core/`'s, each broken alone in a copy of the tree, and what the runner says.

    python3 -B mutants.py <tree> [--staged] [<name> ...]

Every row of `mutants.tsv` beside this script, `name<TAB>file<TAB>old<TAB>new` (`\\n` a newline, `\\t` a tab in a
text), is one edit; the rows sharing a name are one mutant. For the unchanged tree and then each mutant in the
table's order, the tree's COMMITTED `HEAD` is copied (`git archive`) into `$A/mut/<name>/`, and the copy is made a
git checkout of its own, every file staged (`git init`, `git add -A`), since the harness's sweep reads the files git
tracks (`0.0.4.md` step 0c); then each edit is made EXACTLY ONCE -- any other count is a STOP, printed, and that
mutant is not run -- and `harness/run.py` is run in the copy with `$NPKC` and `$NPKRT` from the environment. A row
whose `old` is `<checkout>` writes `new` as a new `file`, in a directory made a git checkout of its own with the file
staged there, which the copy's own index does not hold: a nested checkout, as CI's compiler is at `.nitpick/`. It
prints one line per mutant: `<name>: exit <n> --` and the run's first failing line (a `FAIL` line, else a `failed:`
line, else its `CANNOT PROCEED` line), cut at 200 characters, or its summary when nothing failed. Three run at a
time; the copies are removed at the end. Each mutant breaks ONE facet of one check, so the line names the check that
saw it (`0.0.4.md` §4).

NAMES run those mutants alone, in the table's order, and not the unchanged tree unless `unchanged` is among them,
which runs it first (`0.0.4.md`'s blocks 4m and 4n split the table so that each fits a call); a name the table does
not hold is a STOP, exit 2, before anything is copied. `--staged` copies the tree's INDEX, what its next `git commit`
commits (`git checkout-index`), in place of its `HEAD`: so a part's block runs its mutants over the index with the
patch staged, before the part is committed, and part c's nested checkout over `HEAD` too, the tree before the patch
(`0.0.4.md` §3, step 0).
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKOUT = "<checkout>"


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


def _git(d, *args):
    subprocess.run(["git", "-C", d, *args], check=True, capture_output=True)


def one(tree, base, staged, name, edits):
    d = os.path.join(base, name)
    os.makedirs(d)
    if staged:
        subprocess.run(["git", "-C", tree, "checkout-index", "--all", "--prefix=" + d + os.sep], check=True)
    else:
        arc = subprocess.run(["git", "-C", tree, "archive", "HEAD"], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", d], input=arc, check=True)
    _git(d, "init", "-q")
    _git(d, "add", "-A")
    for f, old, new in edits:
        p = os.path.join(d, f)
        if old == CHECKOUT:
            if os.path.exists(p):
                return f"{name}: STOP -- {f} exists already"
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(new)
            _git(os.path.dirname(p), "init", "-q")
            _git(os.path.dirname(p), "add", "-A")
            continue
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
    unknown = [n for n in names if n not in rows and n != "unchanged"]
    if unknown:
        print("STOP -- mutants.tsv holds no mutant named " + ", ".join(unknown))
        return 2
    shutil.rmtree(base, ignore_errors=True)
    jobs = (([("unchanged", [])] if "unchanged" in names else []) + [(n, rows[n]) for n in order if n in names]
            if names else [("unchanged", [])] + [(n, rows[n]) for n in order])
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        results = list(ex.map(lambda j: one(tree, base, staged, *j), jobs))
    for line in results:
        print(line)
    shutil.rmtree(base, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
