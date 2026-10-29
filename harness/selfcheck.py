#!/usr/bin/env python3
"""The self-check -- the harness fed wrong expectations and required to FAIL (`meta/specs/BUILD.md` B-8,
`TESTING.md` §7; PA-116). It runs FIRST in every full run, and if any live case is not red the run stops
RED there: a suite that only ever agrees with what it is handed reports green while checking nothing.

Every case builds its fixture in `build/harness/selfcheck/<case>/` and hands it to the SAME functions the run
uses -- `stages.Stage`, `stages.check_suite`, `stages.parse_sweep`, `treecheck.*` -- never a copy of their logic.
A LIVE case passes when its function reports the failure it names; a PENDING case is printed as pending, with the
cycle that makes it live, and is never counted as passing. The fixtures' codes are measured at the pin by cycle
0.0.3's plan (`0.0.3.md` §1).
"""
import os
import shutil

import stages
import treecheck

FLOOR = '''func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};
'''
MAIN0 = "func:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n"
TWO_CODES = ("int64:COUNTER = 0i64;\n\nfunc:main = int32(cstring[]:_~argv) {\n    string:s = string_concat(\"ab\", \"c\");\n"
             "    uint8[]:p = string_bytes(s);\n    exit 0i32;\n};\n")
PENDING = [("roundtrip-second-parse-differs", "cycle 0.5, which builds the roundtrip stage"),
           ("roundtrip-trees-match-print-differs", "cycle 0.5 (TESTING.md V-7)"),
           ("corpus-count-off-by-one-both-ways", "cycle 0.3, which builds the corpus stage"),
           ("check_no_owning_fields-planted", "cycle 0.2, when the types it reads exist")]


def _program(d, name, header, body):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name + ".npk")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(header + f"mod:{name};\n\n" + body + "\n" + FLOOR)
    return p


class _Quiet(stages.Stage):
    def _say(self, verdict, suite, rel, detail):
        self.verdicts.append((verdict, suite, rel, detail))


def _stage(ctx, root, floor_bin, floor_edges, pending=None):
    return _Quiet(root, ctx, floor_bin, pending or {}, floor_edges)


def _red(st, want):
    v = [x for x in st.verdicts if x[0] == "FAIL"]
    return (bool(v) and want in v[-1][3]), (v[-1][3] if v else "no FAIL verdict")


def _tree(root, base, files):
    """A scratch tree: the specifications the tree checks read, and the planted `src/` files."""
    os.makedirs(os.path.join(base, "meta", "specs"), exist_ok=True)
    for f in ("BUILD.md", "SAFETY.md"):
        shutil.copy2(os.path.join(root, "meta", "specs", f), os.path.join(base, "meta", "specs", f))
    os.makedirs(os.path.join(base, "harness"), exist_ok=True)
    for rel, text in files.items():
        os.makedirs(os.path.dirname(os.path.join(base, rel)), exist_ok=True)
        with open(os.path.join(base, rel), "w", encoding="utf-8") as fh:
            fh.write(text)
    return base


def cases(ctx, root, floor_bin, floor_edges):
    w = os.path.join(ctx.work, "selfcheck")
    shutil.rmtree(w, ignore_errors=True)
    hdr = "// MAY IMPORT: nothing\n"

    def prog(case, header, body, pending=None, want="expected exit"):
        d = os.path.join(w, case)
        p = _program(d, case.replace("-", "_"), header, body)
        st = _stage(ctx, d, floor_bin, floor_edges, pending)
        st._unit("selfcheck", p, os.path.relpath(p, d))
        return _red(st, want)

    def chk(case, header, body, pending=None, want=""):
        d = os.path.join(w, case)
        _program(d, case.replace("-", "_"), header, body)
        st = _stage(ctx, d, floor_bin, floor_edges, pending)
        stages.check_suite(st, {"name": "selfcheck", "path": "."})
        return _red(st, want)

    def tree(case, check, files, want):
        base = _tree(root, os.path.join(w, case), files)
        _, bad = check(base)
        return (bool(bad) and want in bad[0]), (bad[0] if bad else "no finding")

    out = []
    add = lambda name, r: out.append((name, r[0], r[1]))
    add("program-exit-off-by-one", prog("program-exit-off-by-one", "// expect-exit: 1\n", MAIN0))
    add("check-code-not-reported", chk("check-code-not-reported", "// expect-error: NITPICK-TYPE-007\n",
                                       "int64:COUNTER = 0i64;\n\n" + MAIN0, want="expected and not reported: NITPICK-TYPE-007"))
    add("check-code-unasserted", chk("check-code-unasserted", "// expect-error: NITPICK-TYPE-055\n", TWO_CODES,
                                     want="reported and not expected: NITPICK-TYPE-007"))
    add("check-site-wrong", chk("check-site-wrong", "// expect-error: NITPICK-TYPE-055\n// expect-error-at: 4:1\n",
                                "int64:COUNTER = 0i64;\n\n" + MAIN0, want="expected at 4:1"))
    add("check-accepted", chk("check-accepted", "// expect-error: NITPICK-TYPE-007\n", MAIN0, want="ACCEPTED"))
    d = os.path.join(w, "parse-not-parsing")
    _program(d, "parse_not_parsing", "", "func:main = int32(cstring[]:_~argv) {\n    exit 0i32\n};\n")
    st = _stage(ctx, d, floor_bin, floor_edges)
    stages.parse_sweep(st, {"name": "selfcheck", "path": "."})
    add("parse-not-parsing", _red(st, "NITPICK-PARSE-"))
    add("layering-core-imports-scan", tree("layering-core-imports-scan", treecheck.check_layering, {
        "src/core/a.npk": "mod:a;\n\n// MAY IMPORT: nothing (B-17)\nuse \"../scan/b.npk\".*;\n",
        "src/scan/b.npk": "mod:b;\n\n// MAY IMPORT: `core` (B-17)\n"}, "does not allow"))
    add("error-budget-private-identity", tree("error-budget-private-identity", treecheck.check_error_budget, {
        "src/core/a.npk": "mod:a;\n\nerror:EPrivate;\n\nfunc:f = NIL() {\n    fail EPrivate;\n};\n"}, "`a.EPrivate`"))
    add("constants-bound-literal", tree("constants-bound-literal", treecheck.check_constants_named, {
        "src/scan/a.npk": "mod:a;\n\nfunc:f = int64() never fails {\n    pass 4096i64;\n};\n"}, "the literal 4096"))
    add("raw-accumulate", tree("raw-accumulate", treecheck.check_no_raw_accumulate, {
        "src/scan/a.npk": "mod:a;\n\nfunc:f = int64(int64:acc, int64:d) never fails {\n    pass acc * 10i64 + d;\n};\n"}, "a `*`"))
    add("recursion-self-call", tree("recursion-self-call", treecheck.check_no_recursion, {
        "src/scan/a.npk": "mod:a;\n\nfunc:f = int64(int64:n) {\n    int64:m = relay f(n);\n    pass m;\n};\n"}, "a call cycle: f -> f"))
    marker = "// expect-exit: 0\n// pending-until: DEF-1 undefined-value @x\n"
    add("pending-not-listed", prog("pending-not-listed", marker, MAIN0, want="NOT ON THE REVIEWED PENDING LIST"))
    listed = {("pending_stale.npk", "DEF-1", "undefined-value @x"): "a self-check case"}
    add("pending-stale", prog("pending-stale", marker, MAIN0, listed, want="STALE"))
    other = {("pending_other_failure.npk", "DEF-1", "undefined-value @x"): "a self-check case"}
    add("pending-other-failure", prog("pending-other-failure", marker.replace("expect-exit: 0", "expect-exit: 3"),
                                      MAIN0, other, want="PENDING ON A DIFFERENT FAILURE"))
    acc = {("check_pending_stale.npk", "DEF-1", "accepted"): "a self-check case"}
    add("check-pending-stale", chk("check-pending-stale", "// expect-error: NITPICK-TYPE-055\n// pending-until: DEF-1 accepted\n",
                                   "int64:COUNTER = 0i64;\n\n" + MAIN0, acc, want="STALE"))
    orphan = stages.orphans({("nowhere.npk", "DEF-1", "accepted"): "x"}, set())
    out.append(("pending-list-orphan-line", bool(orphan), orphan[0] if orphan else "no finding"))
    return out


def run(ctx, root, floor_bin, floor_edges, say):
    got = cases(ctx, root, floor_bin, floor_edges)
    for name, red, line in got:
        say(f"{'ok  ' if red else 'FAIL'}  selfcheck {name}: {'red' if red else 'NOT RED'} -- {line[:150]}")
    for name, when in PENDING:
        say(f"PEND  selfcheck {name}: pending until {when}")
    live_red = sum(1 for _, r, _ in got if r)
    return live_red == len(got), f"the self-check: {live_red} of {len(got)} live cases red, {len(PENDING)} pending"
