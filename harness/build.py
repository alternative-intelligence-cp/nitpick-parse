#!/usr/bin/env python3
"""The build, one root at a time -- `meta/specs/BUILD.md` §2 and B-1 … B-3 (PA-113).

ONE MODULE PER ROOT. `npkc` compiles a root and everything it imports into ONE module, so a
program is one object linked with the runtime, `npkrt.o`, and nothing else: there is no
library object to link, and the library root `src/lib.npk` is compiled on its own only to be
scanned and compared (`run.py`'s build steps). Every argv is built from the manifest's
`[toolchain]` lists (B-1); nothing runs at its own defaults.

THE TWO LEGS (B-3): -O0 is `npkc`, `llc` with `llc-flags`, `ld.lld` with `lld-flags`; the
optimised leg re-runs the SAME emission through `opt` with `opt-flags` and `llc` with
`llc-opt-flags`. Each object is scanned (B-2: every undefined symbol defined by the runtime,
since `opt` may mint a libcall); each module's `target triple` and `target datalayout` lines
are held to the manifest's rows (B-1a).

`npkc`'S EXIT ALPHABET, which nothing documents (`PLAYBOOK.md` §6): 0 accepted; 1 REFUSED,
with diagnostics; 2 could not proceed and judged nothing, with an empty stderr; 3 the
compiler's own `failsafe` trap. Only 0 and 1 are verdicts; 2, 3 and anything else are a
broken run, printed with the code itself.
"""
import os
import re
import subprocess

from elf import Obj

_DIAG = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) [^ ]+:([0-9]+):([0-9]+)", re.M)
_UNDEF_VALUE = re.compile(r"use of undefined value '([^']+)'")
_TARGET = re.compile(r'^target (triple|datalayout) = "([^"]*)"$', re.M)


class Leg:
    """One leg of one program: where it stopped, and the binary if it got there."""

    def __init__(self, name):
        self.name, self.stop, self.undefined_value, self.binary = name, None, None, None

    def fail(self, why, undefined_value=None):
        self.stop, self.undefined_value = why, undefined_value
        return self


class Ctx:
    def __init__(self, man, npkc, npkrt, runtime_defined, work):
        tc = man.tables["toolchain"]
        self.npkc, self.npkrt, self.work = npkc, npkrt, work
        self.triple, self.layout = tc["triple"], tc["datalayout"]
        self.llc_flags, self.llc_opt_flags = tc["llc-flags"], tc["llc-opt-flags"]
        self.opt_flags, self.lld_flags = tc["opt-flags"], tc["lld-flags"]
        self.runtime_defined = set(runtime_defined)


def _run(argv, cwd=None, timeout=600):
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return None, f"`{os.path.basename(argv[0])}` did not finish in {timeout} s"


def npkc(ctx, src, out_ll):
    """(exit, [(code, line, col)], text): `npkc` from the root's own directory, as by hand."""
    rc, text = _run([ctx.npkc, os.path.basename(src), "-o", out_ll], cwd=os.path.dirname(src))
    return rc, [(m.group(1), int(m.group(2)), int(m.group(3))) for m in _DIAG.finditer(text)], text


def target_problems(ctx, ll_path, what):
    with open(ll_path, encoding="utf-8", errors="replace") as fh:
        got = dict(_TARGET.findall(fh.read(1 << 16)))
    out = []
    for key, want in (("triple", ctx.triple), ("datalayout", ctx.layout)):
        if got.get(key) != want:
            out.append(f"{what}: `target {key}` is {got.get(key)!r}; nitpick.toml pins {want!r}")
    return out


def undefined_problems(ctx, obj_path, what):
    """B-2: every undefined symbol of the object is one the runtime defines."""
    extra = sorted(set(Obj(obj_path).undefined()) - ctx.runtime_defined)
    return [f"{what}: undefined {', '.join(extra)}, which the runtime does not define "
            "(no C, ever -- B-2)"] if extra else []


def _leg(ctx, name, ll, stem, optimised):
    leg = Leg(name)
    obj, binary = f"{stem}{'.2' if optimised else ''}.o", f"{stem}{'.2' if optimised else ''}"
    if optimised:
        rc, text = _run(["opt", *ctx.opt_flags, ll, "-o", f"{stem}.2.ll"])
        if rc != 0:
            m = _UNDEF_VALUE.search(text)
            return leg.fail(f"opt refused: {text.strip().splitlines()[0][:200] if text.strip() else rc}",
                            m.group(1) if m else None)
        ll = f"{stem}.2.ll"
        bad = target_problems(ctx, ll, "the optimised module")
        if bad:
            return leg.fail("; ".join(bad))
    rc, text = _run(["llc", *(ctx.llc_opt_flags if optimised else ctx.llc_flags), ll, "-o", obj])
    if rc != 0:
        m = _UNDEF_VALUE.search(text)
        return leg.fail(f"llc refused: {text.strip().splitlines()[0][:200] if text.strip() else rc}",
                        m.group(1) if m else None)
    bad = undefined_problems(ctx, obj, f"the {name} object")
    if bad:
        return leg.fail("; ".join(bad))
    rc, text = _run(["ld.lld", *ctx.lld_flags, obj, ctx.npkrt, "-o", binary])
    if rc != 0:
        return leg.fail(f"ld.lld refused: {text.strip()[:200]}")
    leg.binary = binary
    return leg


class Build:
    def __init__(self):
        self.npkc_exit, self.codes, self.text, self.ll, self.legs = None, [], "", None, []


def program(ctx, src, stem):
    """Compile, then both legs. `stem` is the scratch path every artefact is named from."""
    b = Build()
    os.makedirs(os.path.dirname(stem), exist_ok=True)
    b.ll = f"{stem}.ll"
    b.npkc_exit, b.codes, b.text = npkc(ctx, src, b.ll)
    if b.npkc_exit != 0:
        return b
    bad = target_problems(ctx, b.ll, "the emission")
    if bad:
        b.legs = [Leg("-O0").fail("; ".join(bad))]
        return b
    b.legs = [_leg(ctx, "-O0", b.ll, stem, False), _leg(ctx, "-O2", b.ll, stem, True)]
    return b


def npkc_failure(b):
    """The sentence for an `npkc` exit that is not 0."""
    if b.npkc_exit == 1:
        return "npkc REFUSED it: " + (" ".join(f"{c} {l}:{k}" for c, l, k in b.codes) or "no code read")
    if b.npkc_exit == 2:
        return "npkc exit 2 -- the driver could not proceed and judged nothing"
    if b.npkc_exit == 3:
        return "npkc exit 3 -- the compiler's own failsafe trapped"
    return f"npkc exit {b.npkc_exit}"
