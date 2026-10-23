#!/usr/bin/env python3
"""0.0.1a -- the workflow's LLVM install step, run as written against a FAKE asset, both ways (the libraries' seat's
ruling of 2026-10-22 on `ci.yml`'s "an immutable asset"; `nitpick-time` 0.4.0a's block 4 drove its step the same way).

    python3 -B install.py <workflow> <scratch>

The step's `run:` text is read out of the workflow by YAML, never retyped. It runs under `bash` with `LLVM_VERSION`
from the workflow's `env:`, `RUNNER_TEMP` and `HOME` in the scratch (the home named `hm`, which the leak scan cannot
read as a home), and a `curl` first on `PATH` that writes the fake asset -- a deterministic `.tar.xz` holding
`LLVM-<v>-Linux-X64/bin/llc` -- to the `-o` file and fetches nothing. It runs twice:

  1. with the workflow's own `LLVM_TARBALL_SHA256`: the step must exit non-zero before `tar` reads a byte, so nothing
     is unpacked;
  2. with the fake's own sha256: the step must exit 0 and unpack it.

Each run prints its exit, whether `~/llvm/bin/llc` exists after it, and the step's output with the scratch printed as
`<scratch>`, the fake's size as `<n>` and its digest as `<the fake's sha256>`, so no line carries a path or a value that
moves from machine to machine. Writes only under <scratch>, which it clears first.
"""
import hashlib
import io
import lzma
import os
import shutil
import subprocess
import sys
import tarfile

import yaml


def fake_asset(version):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name, data in (("LLVM-%s-Linux-X64/bin/llc" % version, b"#!/bin/sh\necho fake\n"),):
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode, info.uid, info.gid = len(data), 0, 0o755, 0, 0
            tar.addfile(info, io.BytesIO(data))
    return lzma.compress(raw.getvalue(), format=lzma.FORMAT_XZ, preset=6)


def main(argv):
    wf, scratch = argv[1], os.path.realpath(argv[2])
    doc = yaml.safe_load(open(wf, encoding="utf-8"))
    steps = [s for s in doc["jobs"]["build"]["steps"] if str(s.get("name", "")).startswith("Install LLVM")]
    if len(steps) != 1:
        print("the install step: %d step(s) named `Install LLVM ...`" % len(steps))
        return 1
    script, env = steps[0]["run"], doc["env"]
    shutil.rmtree(scratch, ignore_errors=True)
    for d in ("bin", "tmp", "hm"):
        os.makedirs(os.path.join(scratch, d))
    path = os.path.join(scratch, "install.sh")
    open(path, "w", encoding="utf-8").write(script)
    syntax = subprocess.run(["bash", "-n", path], capture_output=True, text=True).returncode
    print("the install step, read from the workflow by YAML: %d line(s); bash -n %s it"
          % (len(script.rstrip("\n").split("\n")), "accepts" if syntax == 0 else "REFUSES"))
    asset = fake_asset(env["LLVM_VERSION"])
    open(os.path.join(scratch, "asset.tar.xz"), "wb").write(asset)
    own = hashlib.sha256(asset).hexdigest()
    curl = os.path.join(scratch, "bin", "curl")
    open(curl, "w", encoding="utf-8").write(
        '#!/usr/bin/env bash\n# the fake: writes the scratch asset to the -o file and fetches nothing\n'
        'out=""; while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then out="$2"; shift; fi; shift; done\n'
        '[ -n "$out" ] || exit 22\ncp "%s" "$out"\n' % os.path.join(scratch, "asset.tar.xz"))
    os.chmod(curl, 0o755)
    for label, digest in (("the workflow's LLVM_TARBALL_SHA256", env["LLVM_TARBALL_SHA256"]),
                          ("the fake's own sha256", own)):
        shutil.rmtree(os.path.join(scratch, "hm"))
        os.makedirs(os.path.join(scratch, "hm"))
        run_env = {"PATH": os.path.join(scratch, "bin") + ":" + os.environ.get("PATH", ""), "LANG": "C",
                   "HOME": os.path.join(scratch, "hm"), "RUNNER_TEMP": os.path.join(scratch, "tmp"),
                   "LLVM_VERSION": str(env["LLVM_VERSION"]), "LLVM_TARBALL_SHA256": digest}
        r = subprocess.run(["bash", path], capture_output=True, text=True, env=run_env)
        unpacked = os.path.isfile(os.path.join(scratch, "hm", "llvm", "bin", "llc"))
        print("the install step over the fake asset, with %s: exit %d; unpacked: %s"
              % (label, r.returncode, "yes" if unpacked else "no"))
        for line in (r.stdout + r.stderr).rstrip("\n").split("\n"):
            line = line.replace(scratch, "<scratch>").replace(own, "<the fake's sha256>")
            line = line.replace("downloaded %d B" % len(asset), "downloaded <n> B")
            print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
