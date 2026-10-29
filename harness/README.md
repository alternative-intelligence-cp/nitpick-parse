# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1) and zero-dependency governs the artifact, not the
workbench. It retires into `npkg` the way `bootstrap/harness/` does in the
compiler repository, with both running side by side and a parity check first.
Built in cycles 0.0.2 and 0.0.3.

*(2026-10-21, cycle 0.0.1:)* until cycle 0.0.2, `run.py` is a stub that builds and judges nothing
and says so; CI runs it so that the workflow's last step exists before the runner does.
*(2026-10-28, cycle 0.0.2: the stub is replaced by the runner below; cycle 0.0.3 adds the
refusal and parse stages, the self-check and the tree checks.)*

```
NPKC=<pinned npkc> NPKRT=<pinned npkrt.o> python3 -B harness/run.py [--verdicts PATH]
```

`$NPKC` and `$NPKRT` are the pinned toolchain the board names (`../../BOARD.md`), and
`llc`, `opt` and `ld.lld` are on `PATH` at the manifest's LLVM exactly. The last line a run
prints is its verdict — `harness: GREEN -- …` or `harness: RED -- …` — and it exits 0, 1, or
2 when it could not proceed. Its scratch is `build/harness/`, cleared when a run starts.

## The modules

| File | What |
|---|---|
| `run.py` | the driver: the manifest and the entries it can honour, the toolchain, three build steps, the suites in manifest order, the reviewed list's other direction, the summary |
| `manifest.py` | `nitpick.toml` in the compiler's subset, held to the compiler's schema at the pin |
| `toolchain.py` | `llc`, `opt`, `ld.lld` at the manifest's LLVM; its `datalayout` the one the pinned `opt` derives (`BUILD.md` B-1a) |
| `expect.py` | the markers a test file carries (B-5, B-5b) |
| `build.py` | one root to one module, both legs, the undefined-symbol scan (B-2), and `npkc`'s exit alphabet |
| `irscan.py` | the call-edge scan, and its two lists that class the runtime's global symbols: DENIED by facet, and FLOOR (B-2a) |
| `elf.py` | an ELF64 symbol table, read with `struct` |
| `stages.py` | the `program` stage and `compile`/`positive`: both legs, `stress`, the cap, and the pending units (B-5b) |
| `baseline/` | the floor program and the syscaller (build step 1, and the cap's control), and `PENDING.txt`, the reviewed list of pending units |

## What a green run asserts

- the manifest names no entry this runner cannot judge, and the toolchain is the pin's;
- the two scans see a syscall — the floor and the syscaller differ by `npk_sys6` alone, and the
  syscaller's `main` is flagged — on this run, at this compiler;
- every module under `src/` compiles as a root with no diagnostic, and none needs a symbol the
  runtime does not define or calls a denied one;
- `[build] entry` and every conformance root emit byte-identical IR from two copies of the tree,
  each with its manifest (B-4);
- every unit of every suite was built at -O0 and through `opt -O2`, its modules stating the
  manifest's target rows, scanned, linked with `npkrt.o` alone, run `stress` times on each leg —
  under its cap after the floor program under the same cap — and exited as it expects; and every
  pending unit showed the one failure its marker names, on every leg, and is a line of
  `baseline/PENDING.txt`, which names no unit that is not pending.
