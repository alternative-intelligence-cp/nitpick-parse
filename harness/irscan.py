#!/usr/bin/env python3
"""The emitted IR's CALL EDGES to the runtime -- `BUILD.md` B-2a (PA-113), the instrument
behind PA-006 and `SAFETY.md` §2, for every facet of theirs a runtime function serves.

WHY CALL EDGES. An undefined-symbol scan reports THAT an object needs a runtime symbol and
never WHERE it is called from; and at an earlier compiler every syscall went through one
symbol the empty program already carried, so a program that made one had the same symbol set
as one that did not (`PLAYBOOK.md`: "the undefined-symbol scan ... CANNOT SEE A SYSCALL"). At
the pin `7e91730` the floor program's object has 5 undefined symbols and a syscaller's 6, the
difference exactly `npk_sys6` (cycle 0.0.2's §1.4) -- and `run.py` re-measures that pair on
every full run, so the day a prelude starts emitting the symbol again the run says so.

WHAT IT SCANS. Every `(enclosing function, callee)` edge in the -O0 IR whose callee is
DECLARED and not DEFINED in the module, `llvm.*` excluded (an intrinsic is an instruction,
never a symbol), the trailing `.<digits>` of compiler-generated glue normalised away (the
counter moves with program content). An edge the floor program does not have, to a DENIED
symbol, is a finding that names the calling function. After `nitpick-regex`'s
`harness/irscan.py`, whose three measured lessons (the intrinsics, the glue's numbering, a
deny list rather than a permit list) this keeps.

THE TWO LISTS CLASS THE RUNTIME WHOLE. At the pin the runtime object defines 119 global symbols,
the only runtime symbols a module's call can reach (a call to a local one does not link), and
each is in exactly one list here: DENIED, by the facet of PA-006 or `SAFETY.md` §2 that forbids
it -- the kernel, a file or descriptor, a process, a signal handler, the clock, the
environment, concurrency (a task, a channel, a lock, a wait, a deadline) and machine code -- or
FLOOR, the language's own machinery any program may reach: the heap, the arena, strings, the
trap route, the stack guard, LLVM's libcalls and the entry. `run.py` holds both to the runtime
object on every run: a name in neither, or one that is not defined, stops it, so a re-pin that
adds or renames a runtime function is classed before a run can be green again (cycle 0.0.2's
plan carries the table, `0.0.2_tools/runtime_symbols.tsv`, with each class's reason).

WHAT IT CANNOT SEE: a facet whose construct lowers to no runtime call -- an atomic operation is
an LLVM instruction, and a mutex or rwlock made and never held is a managed allocation -- what
an allowed function does inside the runtime, and every other way to be platform-specific. A
call-edge scan says nothing of those; review does.
"""
import re

_FAMILIES = (
    ("the kernel", "makes no syscall", (
        "npk_sys6",
        "npk_clone_raw",
    )),
    ("a file or descriptor", "reads no file, opens no descriptor and touches no device", (
        "npk_close", "npk_io_register", "npk_io_unwatch", "npk_ofd_close", "npk_open", "npk_path_exists",
        "npk_read", "npk_read_file", "npk_read_stdin", "npk_write", "npk_write_file",
    )),
    ("a process", "spawns no process", (
        "npk_clone_exec", "npk_driver_kill_all", "npk_driver_live_count", "npk_driver_retire",
    )),
    ("a signal handler", "installs no signal handler", (
        "npk_sigreturn",
    )),
    ("the clock", "has no clock", (
        "npk_mono_now",
    )),
    ("the environment", "has no environment", (
        "npk_environ", "npk_hardware_concurrency",
    )),
    ("concurrency", "has no concurrency: no task, no channel, no lock, no await, no deadline", (
        "npk_barrier_arrive", "npk_barrier_cancel", "npk_barrier_poll", "npk_ch_close", "npk_ch_closed",
        "npk_ch_open", "npk_ch_reclaim", "npk_ch_recv_wait", "npk_ch_send_wait", "npk_ch_try_recv",
        "npk_ch_try_send", "npk_cv_begin", "npk_cv_broadcast", "npk_cv_done", "npk_cv_signal", "npk_exec",
        "npk_frame_alloc", "npk_frame_drain", "npk_frame_exec_destroy", "npk_frame_exec_new", "npk_frame_free",
        "npk_frozen_get", "npk_guard_release", "npk_join_deadline", "npk_mutex_acquire_wait", "npk_park_sleep",
        "npk_park_take", "npk_park_until", "npk_rq_pop", "npk_rq_push", "npk_run_until", "npk_rw_read_wait",
        "npk_rw_release_read", "npk_rw_write_wait", "npk_sarena_bump", "npk_sarena_destroy", "npk_sarena_make",
        "npk_sarena_slot", "npk_sl_earliest", "npk_sl_push", "npk_sl_wake_due", "npk_step", "npk_task_done",
        "npk_thread_entry", "npk_thread_exit", "npk_thread_join", "npk_thread_start", "npk_windup_all",
        "npk_windup_grace", "npk_windup_note",
    )),
    ("machine code", "runs no machine code it made, so nothing in it is x86-64-specific", (
        "npk_wildx_alloc", "npk_wildx_call", "npk_wildx_free", "npk_wildx_seal",
    )),
)
DENIED = frozenset(n for _, _, names in _FAMILIES for n in names)
FACET = {n: (facet, rule) for facet, rule, names in _FAMILIES for n in names}

FLOOR = frozenset((
    # the heap
    "memcpy", "memmove", "memset", "npk_aalloc", "npk_alloc", "npk_alloc_managed", "npk_buffer_new", "npk_calloc",
    "npk_dalloc", "npk_ralloc", "npk_wild_live_count", "npk_wild_release_all",
    # the arena
    "npk_arena_alloc", "npk_arena_at", "npk_arena_destroy", "npk_arena_free", "npk_arena_make", "npk_arena_reset",
    # strings
    "npk_int_to_string", "npk_string_concat", "npk_string_equals", "npk_string_from_bytes", "npk_string_slice",
    "npk_to_cstring",
    # the trap route
    "npk_chain_depth", "npk_chain_push", "npk_chain_reset", "npk_chain_site", "npk_exit", "npk_fs_switch_call",
    "npk_raise", "npk_trap",
    # the stack guard
    "__morestack", "__morestack_non_split", "npk_stack_exhausted", "npk_stack_foreign",
    # LLVM's libcalls
    "__divti3", "__modti3", "__udivti3", "__umodti3", "fmod", "fmodf",
    # the entry
    "_start", "npk_switch_stack",
))

_SYM = r'@(?:"([^"]*)"|([\w.$\-]+))'
_DEFINE = re.compile(r'^\s*define\b.*?' + _SYM + r'\s*\(')
_DECLARE = re.compile(r'^\s*declare\b.*?' + _SYM + r'\s*\(')
_CALL = re.compile(r'\b(?:call|invoke)\b.*?' + _SYM + r'\s*\(')
_GENERATED = re.compile(r'\.\d+$')


def _name(m):
    return m.group(1) if m.group(1) is not None else m.group(2)


def edges(ir_text):
    """{(normalised function, callee)} for every call to a floor symbol."""
    lines = ir_text.split("\n")
    defined, declared = set(), set()
    for line in lines:
        m = _DEFINE.match(line)
        if m:
            defined.add(_name(m))
            continue
        m = _DECLARE.match(line)
        if m:
            declared.add(_name(m))
    floor = {s for s in declared - defined if not s.startswith("llvm.")}
    out, cur = set(), None
    for line in lines:
        m = _DEFINE.match(line)
        if m:
            cur = _name(m)
            continue
        if line.startswith("}"):
            cur = None
            continue
        if cur is None:
            continue
        m = _CALL.search(line)
        if m and _name(m) in floor:
            out.add((_GENERATED.sub(".N", cur), _name(m)))
    return out


def findings(ir_text, baseline, name):
    """One line per denied edge the floor program does not have, naming the function and the facet."""
    return [f"{name}: `{fn}` calls `{callee}`, and the floor program does not -- {FACET[callee][0]}: this "
            f"library {FACET[callee][1]} (PA-006, SAFETY.md §2); a legitimate call is a decision, not an edit here"
            for fn, callee in sorted(edges(ir_text) - baseline) if callee in DENIED]
