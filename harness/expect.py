#!/usr/bin/env python3
"""A test's expectations, read from the test file -- `meta/specs/BUILD.md` B-5 and B-5b.

THE COMPILER'S GRAMMAR, as `npkg/expect.npk` reads it at the pin `7e91730`: a line whose
stripped form starts with `//` is a comment; its body, stripped, is a MARKER when it starts
with a marker's name -- `// see expect-exit: 94` is prose -- and the marker's value is the
WHOLE rest of the line, so `// expect-exit: 94 -- the OutOfBounds arm` cannot be read, and a
test whose expectations cannot be read is a FAILING test, never a silently defaulted one.
`expect-exit:` -- the last one wins, 0 when absent; `stress:` -- 1 when absent;
`expect-error-at: L[:C]` moves the LAST `expect-error:`. (After `nitpick-regex`'s
`harness/expect.py`, which holds the same grammar to the same reader.)

THE MARKERS THE COMPILER'S READER HAS AND THIS RUNNER DOES NOT JUDGE -- `argv:`,
`expect-note:`, `expect-note-at:`, `expect-obligation:`, `explore:`, `explore-seed:`,
`npkc-flags:` -- and this library's two whose stages do not exist yet -- `expect-roundtrip:`
(cycle 0.5) and `expect-fault:` (cycle 0.1 on) -- each make a file UNREADABLE, by name: a
marker a runner ignores is an expectation nobody checks.

THE RUNNER'S OWN TWO (B-5b, PA-114), which `npkg` does not have:

* `mem-cap-mib: N` -- run the program under an N MiB address-space cap, after the floor
  program under the same cap (`stages.py`), because a managed body a free fails to drop is
  invisible to `exit 0` (cycle 0.0.0's probes 09b and 09c);
* `pending-until: DEF-<n> <observation>` -- a unit CORRECT AND RED because the compiler
  defect DEF-<n> is in the pinned compiler. The label is the compiler seat's registration,
  a label nothing resolves; the OBSERVATION is the one failure the marker excuses, and the
  only one, on every leg (`nitpick-regex`'s RX-154 lesson: a marker that excuses any failure
  excuses a different one). At this subcycle the one observation is
  `undefined-value <symbol>`: `npkc` accepts the program and LLVM refuses the module,
  naming that undefined value -- `llc` at -O0, `opt` on the optimised leg.
"""
import re

MARKERS_JUDGED = ("expect-exit:", "expect-error:", "expect-error-at:", "stress:",
                  "mem-cap-mib:", "pending-until:")
MARKERS_REFUSED = ("argv:", "expect-note:", "expect-note-at:", "expect-obligation:",
                   "explore:", "explore-seed:", "npkc-flags:", "expect-roundtrip:",
                   "expect-fault:")
_CODE = re.compile(r"^NITPICK-[A-Z]+-[0-9]{3}$")
_AT = re.compile(r"^([0-9]+)(?::([0-9]+))?$")
_INT = re.compile(r"^-?[0-9]+$")
_LABEL = re.compile(r"^DEF-[0-9]+$")
OBSERVATIONS = ("undefined-value",)


class Expect:
    def __init__(self, path):
        self.path = path
        self.exit = 0
        self.errors = []          # [[code, line or None, col or None]]
        self.stress = 1
        self.mem_cap_mib = None
        self.pending = None       # (label, observation, argument)
        self.problems = []        # each makes the file UNREADABLE

    @property
    def readable(self):
        return not self.problems


def _bad(e, n, why):
    e.problems.append(f"{e.path}:{n}: {why}")
    return e


def read_text(text, path):
    e = Expect(path)
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if not line.startswith("//"):
            continue
        body = line[2:].strip()
        name = next((m for m in MARKERS_JUDGED + MARKERS_REFUSED if body.startswith(m)), None)
        if name is None:
            continue
        value = body[len(name):].strip()
        if name in MARKERS_REFUSED:
            _bad(e, n, f"`{name}` is a marker this runner does not judge at cycle 0.0.2, "
                       "so the expectation would go unchecked")
        elif name == "expect-exit:":
            if not _INT.match(value):
                _bad(e, n, f"`expect-exit: {value}` is not an integer (the value is the "
                           "whole rest of the line)")
                continue
            v = int(value)
            # An exit status is one byte: 321 is reported as 65. A negative value is
            # `npkg`'s "killed by that signal"; Linux has none below -64.
            if v > 255 or v < -64:
                _bad(e, n, f"`expect-exit: {v}` can never be observed: an exit status is "
                           "one byte, and a signal is -1 ... -64")
                continue
            e.exit = v
        elif name == "expect-error:":
            if not _CODE.match(value):
                _bad(e, n, f"`expect-error: {value}` is not a diagnostic code")
                continue
            e.errors.append([value, None, None])
        elif name == "expect-error-at:":
            m = _AT.match(value)
            if not m or not e.errors:
                _bad(e, n, f"`expect-error-at: {value}` -- not `L[:C]`, or no "
                           "`expect-error:` before it")
                continue
            e.errors[-1][1] = int(m.group(1))
            e.errors[-1][2] = int(m.group(2)) if m.group(2) else None
        elif name == "stress:":
            if not _INT.match(value) or int(value) < 1:
                _bad(e, n, f"`stress: {value}` is not a positive integer")
                continue
            e.stress = int(value)
        elif name == "mem-cap-mib:":
            if not _INT.match(value) or int(value) < 1:
                _bad(e, n, f"`mem-cap-mib: {value}` is not a positive integer")
                continue
            e.mem_cap_mib = int(value)
        elif name == "pending-until:":
            parts = value.split(None, 2)
            if (len(parts) != 3 or not _LABEL.match(parts[0])
                    or parts[1] not in OBSERVATIONS):
                _bad(e, n, f"`pending-until: {value}` is not `pending-until: DEF-<n> "
                           f"<observation> <argument>`, the observation one of "
                           f"{', '.join(OBSERVATIONS)}")
                continue
            if e.pending is not None:
                _bad(e, n, "a second `pending-until:` -- a unit waits on one defect")
                continue
            e.pending = (parts[0], parts[1], parts[2])
    return e


def read(path):
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", errors="replace")
    return read_text(text, path)
