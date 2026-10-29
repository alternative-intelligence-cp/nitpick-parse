#!/usr/bin/env python3
"""The `program` stage, and `compile`/`positive` -- `meta/specs/BUILD.md` §3, B-3, B-5, B-5b.

A UNIT is every `.npk` file directly in an entry's `path` (or each of its `paths`; below them
too with `recursive = true`), in name order. Every one is a program, built by `build.py` at
both legs and RUN `stress` times on each, and it PASSES when every run exits with its
`expect-exit:`. Nothing is skipped: a suite's directory holds programs only, and a file with
no `main` fails at the link, by name. `compile`/`positive` is judged the same way, the
optimised leg included, because B-3 runs that leg on every program.

A CAPPED UNIT (`mem-cap-mib: N`) runs under an N MiB address-space cap, and the floor program
runs under the identical cap first and must exit 0: a cap so low that a program allocating
nothing fails it measures the loader, not the unit (`PLAYBOOK.md` §9).

A PENDING UNIT (`pending-until: DEF-<n> <observation> <argument>`, PA-114) is built like
any other, and its verdict is PEND only when the one failure its marker names is what EVERY
leg shows; it is then counted apart from the denominator, as neither a pass nor a failure.
Its -O0 IR is scanned like every unit's, and a call-edge finding there fails it BEFORE that
test: LLVM's refusal of a leg does not unmake a call `npkc` emitted, and a marker excuses one
failure, never a second. It is a FAILURE when it shows anything else, and a FAILURE when it
MEETS its expectation -- the run reddens to say the marker is stale, and its marker and its
line in `harness/baseline/PENDING.txt` go, by the adoption that carries the fix. And every
marker must have its line in that reviewed list, path, label and observation exactly, or the
unit is a failure: a marker is a way for a red to leave a green run, so taking a unit out of
the count is two edits in two files, one of them a reviewed line with a reason
(`nitpick-regex`'s RX-154). `run.py` checks the other direction.
"""
import os
import resource
import subprocess

import build
import expect
import irscan

RUN_TIMEOUT = 600


def _units(root, entry, only=None):
    out = []
    for rel in (entry["paths"] if "paths" in entry else [entry["path"]]):
        top = os.path.join(root, rel)
        if not os.path.isdir(top):
            raise FileNotFoundError(f"[[test]] {entry['name']}: `{rel}` is not a directory")
        if entry.get("recursive"):
            for d, _, fs in sorted(os.walk(top)):
                out += [os.path.join(d, f) for f in sorted(fs) if f.endswith(".npk")]
        else:
            out += [os.path.join(top, f) for f in sorted(os.listdir(top))
                    if f.endswith(".npk") and os.path.isfile(os.path.join(top, f))]
    return [f for f in out if only is None or only in os.path.relpath(f, root)]


def orphans(pending_list, seen):
    """The reviewed list's other direction: a line no pending unit matched."""
    return [f"harness/baseline/PENDING.txt names {k[0]} ({k[1]} {k[2]}), and no pending unit matched it"
            for k in sorted(set(pending_list) - seen)]


def _cap(mib):
    def limit():
        resource.setrlimit(resource.RLIMIT_AS, (mib << 20, mib << 20))
    return limit


def run_binary(path, mib=None):
    try:
        r = subprocess.run([path], capture_output=True, timeout=RUN_TIMEOUT,
                           preexec_fn=_cap(mib) if mib else None)
        return r.returncode
    except subprocess.TimeoutExpired:
        return None


def read_pending_list(root):
    """{(path, label, observation): reason} from the reviewed list."""
    got, p = {}, os.path.join(root, "harness", "baseline", "PENDING.txt")
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) != 4:
                raise ValueError(f"harness/baseline/PENDING.txt: {line.strip()!r} is not "
                                 "path<TAB>label<TAB>observation<TAB>reason")
            got[(cols[0], cols[1], cols[2])] = cols[3]
    return got


class Stage:
    def __init__(self, root, ctx, floor_binary, pending_list, floor_edges, only=None):
        self.root, self.ctx, self.floor, self.floor_edges, self.only = root, ctx, floor_binary, floor_edges, only
        self.pending_list, self.pending_seen, self.floor_under = pending_list, set(), {}
        self.verdicts = []          # (PASS|FAIL|PEND, suite, relpath, detail)

    def _say(self, verdict, suite, rel, detail):
        detail = detail.replace(self.root + os.sep, "")
        self.verdicts.append((verdict, suite, rel, detail))
        print(f"{verdict} {suite}/{os.path.basename(rel)}: {detail}", flush=True)

    def program_suite(self, entry):
        for src in _units(self.root, entry, self.only):
            rel = os.path.relpath(src, self.root)
            self._unit(entry["name"], src, rel)

    def _unit(self, suite, src, rel):
        e = expect.read(src)
        if not e.readable:
            return self._say("FAIL", suite, rel, "UNREADABLE -- " + "; ".join(e.problems))
        if e.errors:
            return self._say("FAIL", suite, rel, "carries `expect-error:`, which a program "
                                                 "stage cannot judge")
        stem = os.path.join(self.ctx.work, suite, os.path.splitext(os.path.basename(src))[0])
        b = build.program(self.ctx, src, stem)
        exits, why, found = {}, None, []
        if b.npkc_exit != 0:
            why = build.npkc_failure(b)
        else:
            with open(b.ll, encoding="utf-8", errors="replace") as fh:
                found = irscan.findings(fh.read(), self.floor_edges, rel)
            stopped = [leg for leg in b.legs if leg.stop]
            if found:
                why = "; ".join(found)
            elif stopped:
                why = "; ".join(f"{leg.name} {leg.stop}" for leg in stopped)
            elif e.mem_cap_mib and not self._floor_ok(e.mem_cap_mib):
                why = (f"under {e.mem_cap_mib} MiB the floor program exits "
                       f"{self.floor_under[e.mem_cap_mib]}: the cap measures the loader")
            else:
                for leg in b.legs:
                    exits[leg.name] = [run_binary(leg.binary, e.mem_cap_mib)
                                       for _ in range(e.stress)]
        if e.pending:
            return self._pending(suite, rel, e, b, exits, why, found)
        if why:
            return self._say("FAIL", suite, rel, why)
        shown = ", ".join(f"{k} {self._show(v)}" for k, v in exits.items())
        if all(x == e.exit for v in exits.values() for x in v):
            return self._say("PASS", suite, rel, shown)
        return self._say("FAIL", suite, rel, f"expected exit {e.exit}; {shown}")

    def _pending(self, suite, rel, e, b, exits, why, found):
        label, observation, arg = e.pending
        key = (rel, label, f"{observation} {arg}".strip())
        marker = f"`pending-until: {label} {observation} {arg}`".replace(" `", "`")
        if key not in self.pending_list:
            return self._say("FAIL", suite, rel, f"{marker} is NOT ON THE REVIEWED PENDING LIST "
                                                 "(harness/baseline/PENDING.txt)")
        self.pending_seen.add(key)
        if found:
            return self._say("FAIL", suite, rel, f"{marker} cannot excuse a call-edge finding -- "
                                                 + "; ".join(found))
        if (observation == "undefined-value" and b.npkc_exit == 0 and b.legs
                and all(leg.stop and leg.undefined_value == arg for leg in b.legs)):
            return self._say("PEND", suite, rel, f"{label} -- every leg refused by LLVM naming "
                                                 f"the undefined value '{arg}', as its marker says")
        if not why and all(x == e.exit for v in exits.values() for x in v):
            return self._say("FAIL", suite, rel, f"STALE {marker}: it now meets its expectation, "
                                                 f"exit {e.exit} at every leg -- {label} is fixed "
                                                 "in this compiler; the marker and its "
                                                 "PENDING.txt line go")
        got = why or ", ".join(f"{k} {self._show(v)}" for k, v in exits.items())
        return self._say("FAIL", suite, rel, f"PENDING ON A DIFFERENT FAILURE -- {marker}; "
                                             f"this tree gives: {got}")

    def _floor_ok(self, mib):
        if mib not in self.floor_under:
            self.floor_under[mib] = run_binary(self.floor, mib)
        return self.floor_under[mib] == 0

    @staticmethod
    def _show(v):
        v = ["hang" if x is None else str(x) for x in v]
        return v[0] if len(v) == 1 else (f"{v[0]} x{len(v)}" if len(set(v)) == 1 else "/".join(v))


# ---- cycle 0.0.3: the refusal stage and the parse sweep (PA-115) ------------------------------------------

def _codes_judged(b_codes, e):
    """B-7: the SET of codes reported equals the set expected; each `expect-error-at` names a site of its code."""
    got = {c for c, _, _ in b_codes}
    want = {c for c, _, _ in e.errors}
    why = []
    if got != want:
        if want - got:
            why.append("expected and not reported: " + " ".join(sorted(want - got)))
        if got - want:
            why.append("reported and not expected: " + " ".join(sorted(got - want)))
    for c, ln, col in e.errors:
        if ln is not None and not any(c == g and ln == gl and (col is None or col == gc) for g, gl, gc in b_codes):
            why.append(f"{c} expected at {ln}:{col if col is not None else '*'}, reported at "
                       + (" ".join(f"{gl}:{gc}" for g, gl, gc in b_codes if g == c) or "no site"))
    return why


def _check_unit(stage, suite, src, rel):
    e = expect.read(src)
    if not e.readable:
        return stage._say("FAIL", suite, rel, "UNREADABLE -- " + "; ".join(e.problems))
    if not e.errors:
        return stage._say("FAIL", suite, rel, "a `check` unit names no `expect-error:` -- nothing it could fail")
    out = os.path.join(stage.ctx.work, suite, os.path.splitext(os.path.basename(src))[0] + ".ll")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rc, codes, text = build.npkc(stage.ctx, src, out)
    shown = " ".join(f"{c} {l}:{k}" for c, l, k in codes)
    if e.pending:
        label, observation, arg = e.pending
        key = (rel, label, observation)
        marker = f"`pending-until: {label} {observation}`"
        if observation != "accepted" or key not in stage.pending_list:
            return stage._say("FAIL", suite, rel, f"{marker} is NOT ON THE REVIEWED PENDING LIST (harness/baseline/PENDING.txt)"
                              if observation == "accepted" else f"{marker} names an observation a `check` unit cannot show")
        stage.pending_seen.add(key)
        if rc == 0 and not text.strip():
            return stage._say("PEND", suite, rel, f"{label} -- accepted by npkc, exit 0, no diagnostic, as its marker says")
        if rc == 1 and not _codes_judged(codes, e):
            return stage._say("FAIL", suite, rel, f"STALE {marker}: it is now refused with exactly its codes ({shown}) -- "
                                                  f"{label} is fixed in this compiler; the marker and its PENDING.txt line go")
        return stage._say("FAIL", suite, rel, f"PENDING ON A DIFFERENT FAILURE -- {marker}; npkc exit {rc}: {shown or 'no code'}")
    if rc == 0:
        return stage._say("FAIL", suite, rel, "ACCEPTED by npkc -- its expectations name a refusal")
    if rc != 1:
        return stage._say("FAIL", suite, rel, f"npkc exit {rc} -- " + ("the driver could not proceed and judged nothing"
                                               if rc == 2 else "the compiler's own failsafe trapped" if rc == 3 else "not a verdict"))
    why = _codes_judged(codes, e)
    return stage._say("FAIL" if why else "PASS", suite, rel, "; ".join(why) if why else f"refused: {shown}")


def check_suite(stage, entry):
    for src in _units(stage.root, entry, stage.only):
        _check_unit(stage, entry["name"], src, os.path.relpath(src, stage.root))


SWEEP_SKIP = {".git", "build", ".internal"}


def parse_sweep(stage, entry):
    """Every `.npk` under the entry's path, each compiled as a root by `npkc` and judged by its diagnostics' FAMILY:
    it parses unless a `NITPICK-LEX-` or `NITPICK-PARSE-` code is reported, or `npkc` could not proceed (exit 2 or
    3). A file refused for its types, its borrows or its reach parses -- `refused/` holds such files on purpose."""
    files = []
    for rel in (entry["paths"] if "paths" in entry else [entry["path"]]):
        for d, dirs, fs in os.walk(os.path.join(stage.root, rel)):
            dirs[:] = sorted(x for x in dirs if x not in SWEEP_SKIP)
            files += [os.path.join(d, f) for f in sorted(fs) if f.endswith(".npk")]
    bad = []
    for src in files:
        out = os.path.join(stage.ctx.work, "sweep", os.path.relpath(src, stage.root)[:-4].replace(os.sep, "_") + ".ll")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        rc, codes, _ = build.npkc(stage.ctx, src, out)
        fam = sorted({c for c, _, _ in codes if c.startswith(("NITPICK-LEX-", "NITPICK-PARSE-"))})
        if rc not in (0, 1) or fam:
            bad.append(f"{os.path.relpath(src, stage.root)}: " + (" ".join(fam) if fam else f"npkc exit {rc}"))
    rel = entry["paths"][0] if "paths" in entry else entry["path"]
    stage._say("FAIL" if bad else "PASS", entry["name"], rel,
               (f"{len(files)} file(s) swept; " + "; ".join(bad)) if bad else
               f"{len(files)} file(s) swept, each compiled as a root, none with a LEX- or PARSE- code")
