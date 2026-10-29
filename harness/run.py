#!/usr/bin/env python3
"""nparse's build and test runner, until `npkg` can build a library (PA-003).

    NPKC=<pinned npkc> NPKRT=<pinned npkrt.o> python3 -B harness/run.py [--verdicts PATH]

WHAT A RUN DOES, IN ORDER, and every step can fail it:

1. reads `nitpick.toml` (`manifest.py`) and REFUSES BY NAME, before anything runs, an entry
   this runner cannot honour -- at cycle 0.0.2 it judges `program` and `compile`/`positive`
   entries, and `[build] opt-level = 0` -- exit 2, never a skip (the compiler's
   `BUILD_REFERENCE.md` §7.1 rule);
2. holds the toolchain to the manifest (`toolchain.py`): `llc`, `opt` and `ld.lld` at its
   LLVM exactly, its datalayout the one the pinned `opt` derives from its triple, `$NPKC`
   and `$NPKRT` set -- and holds `irscan.py`'s two lists to `$NPKRT`: every name in them
   defined, and every global symbol it defines in one of them -- exit 2 otherwise;
3. three BUILD STEPS (`meta/specs/BUILD.md` B-2, B-2a, B-4; PA-113): the scans' own
   controls -- the floor program and a syscaller from `harness/baseline/`, whose objects
   must differ by `npk_sys6` alone and whose call edges the scan must flag in the
   syscaller's `main` and nowhere in the floor's, so a blind scan reddens the run; the
   library -- every module under `src/`, each compiled as a root on its own and scanned, the
   entry's artefacts left at `[build] output`; and REPRO -- `[build] entry` and every
   conformance root built from two copies of the tree, each carrying its manifest, their IR
   compared byte for byte;
4. the suites, in manifest order (`stages.py`), every unit's -O0 IR scanned for call edges
   the floor program lacks to a symbol `irscan.py` denies;
5. holds `harness/baseline/PENDING.txt` to the pending units, the other direction: a line
   no pending unit matched is a failure.

It prints one line per step and unit, and LAST, the summary -- `harness: GREEN -- …` when
nothing failed, `harness: RED -- …` otherwise -- and exits 0 on GREEN, 1 on RED and 2 when it
could not proceed. Its scratch is `build/harness/`, cleared at the start of each run and left
at its end; `[build] entry`'s artefacts are `[build] output` with `.ll` and `.o`.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build      # noqa: E402
import irscan     # noqa: E402
import manifest   # noqa: E402
import stages     # noqa: E402
import toolchain  # noqa: E402
from elf import Obj  # noqa: E402

ROOT = os.path.dirname(HERE)
JUDGED = {("program", None), ("compile", "positive")}


def out(line):
    """Every line the runner prints: no path above the repository reaches a log or a record."""
    print(line.replace(ROOT + os.sep, ""), flush=True)


def stop(why):
    out(f"harness: CANNOT PROCEED -- {why}")
    sys.exit(2)


def honour(man):
    for t in man.tests:
        if (t["stage"], t.get("kind")) not in JUDGED:
            stop(f"[[test]] `{t['name']}` is stage `{t['stage']}`"
                 f"{', kind `' + t['kind'] + '`' if 'kind' in t else ''}, which this runner does "
                 "not judge at cycle 0.0.2 -- refused by name, never skipped")
    if man.need("build", "opt-level") != 0:
        stop("[build] opt-level is not 0 -- raising it is its own decision, and this runner "
             "honours 0 only")


def baseline(ctx, failures):
    """The scans' controls: floor and syscaller, both built, both run, and their difference."""
    got = {}
    for name in ("floor", "syscaller"):
        b = build.program(ctx, os.path.join(ROOT, "harness", "baseline", f"{name}.npk"),
                          os.path.join(ctx.work, "baseline", name))
        if b.npkc_exit != 0 or any(leg.stop for leg in b.legs):
            failures.append(f"baseline {name}: " + (build.npkc_failure(b) if b.npkc_exit
                            else "; ".join(f"{leg.name} {leg.stop}" for leg in b.legs if leg.stop)))
            return None, None
        if stages.run_binary(b.legs[0].binary) != 0:
            failures.append(f"baseline {name}: does not exit 0")
            return None, None
        with open(b.ll, encoding="utf-8", errors="replace") as fh:
            got[name] = (set(Obj(b.legs[0].binary + ".o").undefined()), fh.read(), b.legs[0].binary)
    floor_undef, floor_ir, floor_bin = got["floor"]
    sys_undef, sys_ir, _ = got["syscaller"]
    floor_edges = irscan.edges(floor_ir)
    diff = sorted(sys_undef ^ floor_undef)
    flagged = irscan.findings(sys_ir, floor_edges, "syscaller")
    ok = diff == ["npk_sys6"] and len(flagged) == 1 and "`main` calls `npk_sys6`" in flagged[0]
    ok = ok and not irscan.findings(floor_ir, floor_edges, "floor")
    out(f"{'ok  ' if ok else 'FAIL'}  build step 1, the scans' controls: the floor program has "
        f"{len(floor_undef)} undefined symbols and {len(floor_edges)} call edges to the floor; the "
        f"syscaller differs by {' '.join(diff) or 'nothing'}, and the call-edge scan flags "
        f"{len(flagged)} edge(s) in it")
    if not ok:
        failures.append("build step 1: the no-syscall instruments did not see the syscaller "
                        "exactly -- a blind scan passes everything")
    return floor_edges, floor_bin


def library(ctx, man, floor_edges, failures):
    """B-2 and B-2a over the library: EVERY module under `src/`, each compiled as a root on its
    own -- `[build] entry` reaches only what it imports, and a module it does not import yet
    is library code all the same -- and the entry's artefacts left at `[build] output`."""
    entry, output = man.need("build", "entry"), man.need("build", "output")
    os.makedirs(os.path.dirname(os.path.join(ROOT, output)), exist_ok=True)
    mods = sorted(os.path.relpath(os.path.join(d, f), ROOT)
                  for d, _, fs in os.walk(os.path.join(ROOT, "src")) for f in fs if f.endswith(".npk"))
    if entry not in mods:
        failures.append(f"build step 2: [build] entry {entry} is not a module under src/")
    bad = []
    for rel in mods:
        stem = os.path.join(ROOT, output) if rel == entry else os.path.join(ctx.work, "src", rel[:-4])
        os.makedirs(os.path.dirname(stem), exist_ok=True)
        ll, obj = stem + ".ll", stem + ".o"
        rc, codes, text = build.npkc(ctx, os.path.join(ROOT, rel), ll)
        if rc != 0 or text.strip():
            bad.append(f"{rel}: npkc exit {rc}" + (": " + " ".join(c for c, _, _ in codes) if codes else ""))
            continue
        bad += build.target_problems(ctx, ll, rel)
        r = build._run(["llc", *ctx.llc_flags, ll, "-o", obj])
        if r[0] != 0:
            bad.append(f"{rel}: llc refused it")
            continue
        bad += build.undefined_problems(ctx, obj, rel)
        with open(ll, encoding="utf-8", errors="replace") as fh:
            bad += irscan.findings(fh.read(), floor_edges, rel)
    out(f"{'ok  ' if not bad else 'FAIL'}  build step 2, the library: {len(mods)} module(s) under src/, "
        f"each compiled as a root and scanned{', no finding' if not bad else ': ' + '; '.join(bad)}")
    failures += [f"build step 2: {b}" for b in bad]


def repro(ctx, man, failures):
    """B-4: the same tree from two directories, each copy with its manifest (D-236)."""
    entry = man.need("build", "entry")
    base = os.path.join(ctx.work, "repro")
    roots = [entry] + sorted(os.path.join("tests", "conformance", f)
                             for f in os.listdir(os.path.join(ROOT, "tests", "conformance"))
                             if f.endswith(".npk"))
    copies = [os.path.join(base, "a"), os.path.join(base, "bb", "deeper")]
    for c in copies:
        os.makedirs(c)
        shutil.copy2(os.path.join(ROOT, "nitpick.toml"), c)
        shutil.copytree(os.path.join(ROOT, "src"), os.path.join(c, "src"))
        shutil.copytree(os.path.join(ROOT, "tests", "conformance"),
                        os.path.join(c, "tests", "conformance"))
    differ = []
    for r in roots:
        texts = []
        for k, c in enumerate(copies):
            ll = os.path.join(base, f"{k}.{r.replace(os.sep, '_')}.ll")
            rc, _, _ = build.npkc(ctx, os.path.join(c, r), ll)
            texts.append(open(ll, "rb").read() if rc == 0 else None)
        if texts[0] is None or texts[0] != texts[1]:
            differ.append(r)
    out(f"{'ok  ' if not differ else 'FAIL'}  build step 3, repro: {len(roots)} root(s) from two "
        f"directories, {'byte-identical IR' if not differ else 'DIFFERENT IR: ' + ' '.join(differ)}")
    failures += [f"build step 3: {r} emits different IR from two directories (B-4)" for r in differ]


def main(argv):
    verdicts_path = None
    if argv[1:2] == ["--verdicts"] and len(argv) == 3:
        verdicts_path = argv[2]
    elif len(argv) != 1:
        stop("usage: run.py [--verdicts PATH]")
    try:
        man = manifest.read(os.path.join(ROOT, "nitpick.toml"))
    except manifest.ManifestError as e:
        stop(str(e))
    honour(man)
    try:
        toolchain.check(man.need("toolchain", "llvm"), out)
        toolchain.check_target(man.need("toolchain", "triple"),
                               man.need("toolchain", "datalayout"), out)
        npkc, npkrt = toolchain.compiler(out)
    except (toolchain.ToolchainError, manifest.ManifestError) as e:
        stop(str(e))
    runtime_defined = Obj(npkrt).defined()
    rt = Obj(npkrt)
    missing = sorted((irscan.DENIED | irscan.FLOOR) - set(rt.defined()))
    if missing:
        stop(f"irscan.py names {', '.join(missing)}, which the runtime does not define -- "
             "its lists are stale for this compiler")
    unclassed = sorted(set(rt.exported()) - irscan.DENIED - irscan.FLOOR)
    if unclassed:
        stop(f"the runtime defines {', '.join(unclassed)}, which irscan.py classes neither DENIED nor FLOOR -- "
             "class each by PA-006 and SAFETY.md §2 before the call-edge scan stands behind it")
    work = os.path.join(ROOT, "build", "harness")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    ctx = build.Ctx(man, npkc, npkrt, runtime_defined, work)
    failures = []
    floor_edges, floor_bin = baseline(ctx, failures)
    if floor_edges is None:
        out("harness: RED -- " + "; ".join(failures))
        return 1
    library(ctx, man, floor_edges, failures)
    repro(ctx, man, failures)
    try:
        pending_list = stages.read_pending_list(ROOT)
    except (OSError, ValueError) as e:
        stop(str(e))
    st = stages.Stage(ROOT, ctx, floor_bin, pending_list, floor_edges)
    for t in man.tests:
        st.program_suite(t)
    for key in sorted(set(pending_list) - st.pending_seen):
        failures.append(f"harness/baseline/PENDING.txt names {key[0]} ({key[1]} {key[2]}), and no "
                        "pending unit matched it")
    n = {v: sum(1 for x in st.verdicts if x[0] == v) for v in ("PASS", "FAIL", "PEND")}
    failures += [f"{s}/{os.path.basename(r)}" for v, s, r, _ in st.verdicts if v == "FAIL"]
    if verdicts_path:
        with open(verdicts_path, "w", encoding="utf-8") as fh:
            for v, s, r, d in st.verdicts:
                fh.write(f"{v}\t{s}\t{r}\t{d}\n")
    labels = sorted({d.split(" ", 1)[0] for v, _, _, d in st.verdicts if v == "PEND"})
    judged = n["PASS"] + n["FAIL"]
    tail = (f"{n['PASS']} of {judged} units passed, {n['PEND']} pending"
            f"{' (' + ', '.join(labels) + ')' if labels else ''}")
    if failures:
        for f in failures:
            out(f"  failed: {f}")
        out(f"harness: RED -- {len(failures)} failure(s); {tail}")
        return 1
    out(f"harness: GREEN -- 3 build steps; {tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
