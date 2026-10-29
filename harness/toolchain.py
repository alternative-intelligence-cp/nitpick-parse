#!/usr/bin/env python3
"""The toolchain is a build input (the compiler's D-204), so it is ASSERTED, not reported.

The manifest pins a patch release, so every check is exact: a patch release may change
instruction selection (PA-111). It asks the three tools that run -- `llc`, `opt` and
`ld.lld` -- and not `llvm-config`, a `-dev` package the build does not need. And it
holds the manifest's `datalayout` to what the pinned `opt` derives from its `triple`, since
`opt` keeps a wrong layout as written and `llc` accepts one in silence (`BUILD.md` B-1a,
PA-113). After `nitpick-regex`'s `harness/toolchain.py`.
"""
import os
import re
import subprocess


class ToolchainError(Exception):
    pass


_VERSION = re.compile(r"\b(\d+\.\d+\.\d+)\b")
_LAYOUT = re.compile(r'^target datalayout = "([^"]*)"$', re.M)


def _ask(tool):
    try:
        r = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise ToolchainError(f"`{tool}` is not on PATH -- it is one of the three binaries "
                             "nitpick.toml [toolchain] pins, and a check skipped because "
                             "its tool is missing is how a defect ships")
    except subprocess.TimeoutExpired:
        raise ToolchainError(f"`{tool} --version` did not answer in 30 s")
    m = _VERSION.search(r.stdout + r.stderr)
    if not m:
        raise ToolchainError(f"`{tool} --version` printed no version: "
                             f"{(r.stdout + r.stderr).strip()[:120]!r}")
    return m.group(1)


def check(llvm, out):
    for tool in ("llc", "opt", "ld.lld"):
        got = _ask(tool)
        if got != llvm:
            raise ToolchainError(f"`{tool}` is {got} and nitpick.toml [toolchain] llvm pins "
                                 f"{llvm} exactly -- a refusal, not a warning (D-204)")
        out(f"ok    {tool} {got}")


def check_target(triple, datalayout, out):
    try:
        r = subprocess.run(["opt", "-S", "-"], input=f'target triple = "{triple}"\n',
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise ToolchainError(f"`opt -S` over the triple probe failed: {e}")
    m = _LAYOUT.search(r.stdout)
    if r.returncode != 0 or not m:
        raise ToolchainError("`opt -S` over a module stating only the pinned triple wrote no "
                             f"`target datalayout`: {(r.stderr or r.stdout).strip()[:160]!r}")
    if m.group(1) != datalayout:
        raise ToolchainError(f"nitpick.toml pins the layout {datalayout!r}, and the pinned "
                             f"`opt` derives {m.group(1)!r} from the triple {triple!r}")
    out(f"ok    target {triple}, its layout the one the pinned opt derives")


def compiler(out):
    """`$NPKC` and `$NPKRT`: the pinned pair the board names (W-18)."""
    got = []
    for var, what in (("NPKC", "the pinned npkc binary"),
                      ("NPKRT", "the pinned npkrt.o runtime object")):
        p = os.environ.get(var, "")
        if not p:
            raise ToolchainError(f"${var} is not set; it must name {what} -- from the dispatch, "
                                 "or by hand from `../.internal/toolchain/<commit>/`")
        if not os.path.isfile(p):
            raise ToolchainError(f"${var} names no file")
        got.append(os.path.abspath(p))
        out(f"ok    ${var} is a file")
    return got[0], got[1]
