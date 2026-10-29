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
It is a FAILURE when it shows anything else, and a FAILURE when it MEETS its expectation --
the run reddens to say the marker is stale, and its marker and its line in
`harness/baseline/PENDING.txt` go, by the adoption that carries the fix. And every marker
must have its line in that reviewed list, path, label and observation exactly, or the unit is
a failure: a marker is a way for a red to leave a green run, so taking a unit out of the
count is two edits in two files, one of them a reviewed line with a reason (`nitpick-regex`'s
RX-154). `run.py` checks the other direction.
"""
import os
import resource
import subprocess

import build
import expect
import irscan

RUN_TIMEOUT = 600


def _units(root, entry):
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
    return out


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
    def __init__(self, root, ctx, floor_binary, pending_list, floor_edges):
        self.root, self.ctx, self.floor, self.floor_edges = root, ctx, floor_binary, floor_edges
        self.pending_list, self.pending_seen, self.floor_under = pending_list, set(), {}
        self.verdicts = []          # (PASS|FAIL|PEND, suite, relpath, detail)

    def _say(self, verdict, suite, rel, detail):
        detail = detail.replace(self.root + os.sep, "")
        self.verdicts.append((verdict, suite, rel, detail))
        print(f"{verdict} {suite}/{os.path.basename(rel)}: {detail}", flush=True)

    def program_suite(self, entry):
        for src in _units(self.root, entry):
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
        exits, why = {}, None
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
            return self._pending(suite, rel, e, b, exits, why)
        if why:
            return self._say("FAIL", suite, rel, why)
        shown = ", ".join(f"{k} {self._show(v)}" for k, v in exits.items())
        if all(x == e.exit for v in exits.values() for x in v):
            return self._say("PASS", suite, rel, shown)
        return self._say("FAIL", suite, rel, f"expected exit {e.exit}; {shown}")

    def _pending(self, suite, rel, e, b, exits, why):
        label, observation, arg = e.pending
        key = (rel, label, f"{observation} {arg}")
        marker = f"`pending-until: {label} {observation} {arg}`"
        if key not in self.pending_list:
            return self._say("FAIL", suite, rel, f"{marker} is NOT ON THE REVIEWED PENDING LIST "
                                                 "(harness/baseline/PENDING.txt)")
        self.pending_seen.add(key)
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
