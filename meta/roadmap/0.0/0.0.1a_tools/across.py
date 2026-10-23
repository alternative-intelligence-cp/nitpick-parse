#!/usr/bin/env python3
"""0.0.1a -- the old-pin leg (W-31): every `.npk` of one tree, at the kept pin and at the new one.

    python3 -B across.py <tree> <old pin> <new pin> <compiler tree>      (and env.sh's NPKC, NPKRT, NPKC_OLD,
                                                                          NPKRT_OLD and A)

ONE TREE AT TWO PINS (the workbench `PLAYBOOK.md` §12: compare emissions across pins over one tree). Each tracked `.npk`
is compiled as a root from its own directory by each pin's `npkc`, as `env.sh`'s `codes` compiles one:

  * the VERDICT -- `compiles`, or the set of codes at their sites -- must be the same at both pins; a file whose
    verdict moved is printed with both;
  * the EMISSION of every file that compiles at both is compared through the compiler's own normaliser for the one
    landing between the pins that moves every emission's text, landing 126 (DEF-242: the site table holds the sites
    the emission holds, its ids renumbered dense, the tables cut to the program's own; DEF-263: `npk_site_path`
    answers a view). The tool is `meta/roadmap/1.6/tools/sitenorm.py`, read at the NEW pin with `git show` and run
    as written with `--site-path-cap`, which is the reading the compiler's notice for 126 gives for a comparison
    across it; its two prelude arguments are each pin's `src/prelude/prelude.npk`. Its own lines are printed
    verbatim: one per pair, `IDENTICAL`, `SAME` (with the site counts at each pin) or `DIFF`, then its `SUMMARY`
    and `RESIDUE`;
  * every PROGRAM (a file with `func:main`) that compiles at both is linked and run at -O0 and through `opt -O2` by
    each pin's toolchain, under the address-space cap its `// mem-cap-mib:` line names, and its four exits are
    printed; the two pins must give the same exit at each leg.

Writes only under `$A/across`, which it clears first.
"""
import os
import re
import resource
import shutil
import subprocess
import sys

CODE = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) [^ ]*:([0-9]+:[0-9]+)", re.M)


def env(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit("STOP: %s is not set -- source env.sh first" % name)
    return v


def run(cmd, cwd=None, cap=None, timeout=600):
    def limit():
        if cap:
            n = cap * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (n, n))
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, preexec_fn=limit if cap else None,
                          timeout=timeout)


def compile_one(npkc, path, out):
    r = run([npkc, os.path.basename(path), "-o", out], cwd=os.path.dirname(path))
    text = r.stdout + r.stderr
    if r.returncode == 0 and not text.strip():
        return "compiles"
    return "npkc %d -- %s" % (r.returncode, " ".join("%s %s" % m for m in CODE.findall(text)))


def legs(npkrt, ll, out, cap):
    """The exits at -O0 and through `opt -O2`, or the stage that refused."""
    exits = []
    for leg in ("0", "2"):
        src = ll
        if leg == "2":
            src = out + ".2.ll"
            if run(["opt", "-O2", "-S", ll, "-o", src]).returncode:
                return "opt refused"
        obj, exe = out + ".%s.o" % leg, out + ".%s" % leg
        if run(["llc", "-O" + leg, "-filetype=obj", "-relocation-model=static", src, "-o", obj]).returncode:
            return "llc -O%s refused" % leg
        if run(["ld.lld", "-static", obj, npkrt, "-o", exe]).returncode:
            return "ld.lld -O%s refused" % leg
        exits.append(str(run([exe], cap=cap).returncode))
    return "-O0 %s, -O2 %s" % tuple(exits)


def main(argv):
    tree = os.path.realpath(argv[1])
    pins = [("old", argv[2], env("NPKC_OLD"), env("NPKRT_OLD")), ("new", argv[3], env("NPKC"), env("NPKRT"))]
    npk_tree, scratch = argv[4], os.path.join(env("A"), "across")
    shutil.rmtree(scratch, ignore_errors=True)
    pairs = os.path.join(scratch, "pairs")
    os.makedirs(pairs)
    for side, pin, _, _ in pins:
        src = subprocess.run(["git", "-C", npk_tree, "show", "%s:src/prelude/prelude.npk" % pin],
                             capture_output=True, text=True, check=True).stdout
        open(os.path.join(scratch, "prelude.%s.npk" % side), "w", encoding="utf-8").write(src)
    tool = os.path.join(scratch, "sitenorm.py")
    open(tool, "w", encoding="utf-8").write(subprocess.run(
        ["git", "-C", npk_tree, "show", "%s:meta/roadmap/1.6/tools/sitenorm.py" % pins[1][1]],
        capture_output=True, text=True, check=True).stdout)

    files = sorted(subprocess.run(["git", "-C", tree, "ls-files", "*.npk"], capture_output=True, text=True,
                                  check=True).stdout.split())
    verdict, both = {}, []
    for f in files:
        name = f.replace("/", "__")[:-len(".npk")]
        got = [compile_one(npkc, os.path.join(tree, f), os.path.join(pairs, "%s.%s.ll" % (name, side)))
               for side, _, npkc, _ in pins]
        verdict[f] = got
        if got[0] == got[1] == "compiles":
            both.append((f, name))
    refused = [f for f in files if verdict[f][0] == verdict[f][1] != "compiles"]
    moved = [f for f in files if verdict[f][0] != verdict[f][1]]
    print("across %s and %s: %d .npk file(s) of the tree, each compiled as a root from its own directory by each "
          "pin's npkc" % (pins[0][1], pins[1][1], len(files)))
    print("  verdicts: %d compile at both pins; %d refused at both with the same codes at the same sites; %d moved"
          % (len(both), len(refused), len(moved)))
    for f in moved:
        print("  MOVED %s: at %s %s; at %s %s" % (f, pins[0][1], verdict[f][0], pins[1][1], verdict[f][1]))
    for f in files:
        if f not in [b[0] for b in both]:
            for side in ("old", "new"):
                p = os.path.join(pairs, "%s.%s.ll" % (f.replace("/", "__")[:-len(".npk")], side))
                if os.path.exists(p):
                    os.remove(p)
    print("  the emissions of the %d, through the compiler's sitenorm.py --site-path-cap, read at %s:"
          % (len(both), pins[1][1]))
    r = run(["python3", "-B", "-I", tool, os.path.join(scratch, "prelude.old.npk"),
             os.path.join(scratch, "prelude.new.npk"), pairs, ".old.ll", ".new.ll", "--site-path-cap"])
    for line in (r.stdout + r.stderr).rstrip("\n").split("\n"):
        print("    " + line)
    programs = [(f, name) for f, name in both if re.search(r"^func:main\b", open(os.path.join(tree, f),
                                                                                  encoding="utf-8").read(), re.M)]
    same = 0
    lines = []
    for f, name in programs:
        text = open(os.path.join(tree, f), encoding="utf-8").read()
        m = re.search(r"^// mem-cap-mib: (\d+)", text, re.M)
        cap = int(m.group(1)) if m else None
        got = [legs(npkrt, os.path.join(pairs, "%s.%s.ll" % (name, side)), os.path.join(scratch, "%s.%s" % (name, side)),
                    cap) for side, _, _, npkrt in pins]
        same += got[0] == got[1]
        lines.append("    %s%s: at %s %s; at %s %s%s" % (f, " (cap %d MiB)" % cap if cap else "", pins[0][1], got[0],
                                                      pins[1][1], got[1], "" if got[0] == got[1] else "  MOVED"))
    print("  programs linked with each pin's npkrt.o and run at -O0 and through opt -O2: %d; the same exits at both "
          "pins: %d" % (len(programs), same))
    print("\n".join(lines))
    return 0 if not moved and same == len(programs) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
