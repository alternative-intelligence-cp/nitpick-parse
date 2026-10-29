#!/usr/bin/env python3
"""The tree checks -- the library diffed against the documents that describe it (`meta/specs/TESTING.md` §5,
PA-117). Each reads its AUTHORITY from the specification, not from a copy of it here, and prints what it
examined, so a check that had nothing to read says so rather than passing in silence. Every one but
`check_specs_current` fails the run. Source is read as `shapes.py` reads it: bytes, comments and strings blanked.

  check_layering           every `use` edge between `src/` layers, and every module header's `MAY IMPORT:` line,
                           against `BUILD.md` B-17's table
  check_error_budget       the identities the tree's `fail` sites raise, keyed by (module, name), private ones
                           included, against `SAFETY.md` §3's table and S-6's layers (the ecosystem audit's EC3)
  check_constants_named    no integer literal under `src/` outside `src/core/limits.npk` equal to a bound of
                           `SAFETY.md` §7's table, in any spelling; and limits.npk's values the table's
  check_no_raw_accumulate  no `*`, and no `x = x + <a non-literal>`, under `src/scan/` and `src/format/` outside
                           `arith.npk` (PA-012)
  check_no_recursion       no cycle in the call graph of the functions under `src/` (PA-022); the exceptions
                           table is empty and stays empty at 1.0
  check_specs_current      REPORTS, never fails: a rule id a `src/` or `harness/` comment cites that no
                           specification defines
"""
import os
import re

from lexical import blank as _blank


def _src_files(root):
    out = []
    for d, dirs, fs in os.walk(os.path.join(root, "src")):
        dirs.sort()
        out += [os.path.join(d, f) for f in sorted(fs) if f.endswith(".npk")]
    return out


def _read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


def _layer(root, path):
    rel = os.path.relpath(path, os.path.join(root, "src")).split(os.sep)
    return rel[0] if len(rel) > 1 else "lib"


def check_layering(root):
    spec = _read(os.path.join(root, "meta", "specs", "BUILD.md"))
    sec = spec[spec.index("**Rule B-17"):spec.index("**Rule B-18")]
    table = {}
    for m in re.finditer(r"^\| `(\w+)` \| (.+?) \|$", sec, re.M):
        table[m.group(1)] = set(re.findall(r"`(\w+)`", m.group(2)))
    bad, edges, files = [], 0, _src_files(root)
    for f in files:
        layer, raw = _layer(root, f), _read(f)
        if layer == "lib":
            continue
        head = re.search(r"^// MAY IMPORT: (.+)$", raw, re.M)
        want = table.get(layer)
        if want is None:
            bad.append(f"{os.path.relpath(f, root)}: layer `{layer}` has no row in B-17's table")
            continue
        if head is None:
            bad.append(f"{os.path.relpath(f, root)}: no `// MAY IMPORT:` header line")
        elif set(re.findall(r"`(\w+)`", head.group(1).split("(")[0])) != want:
            bad.append(f"{os.path.relpath(f, root)}: its header names {head.group(1).split('(')[0].strip()!r}, B-17's row {sorted(want) or 'nothing'}")
        for m in re.finditer(r'\buse\s+"([^"]+)"', raw):
            target = os.path.normpath(os.path.join(os.path.dirname(f), m.group(1)))
            if not target.startswith(os.path.join(root, "src") + os.sep):
                continue
            edges += 1
            to = _layer(root, target)
            if to != layer and to not in want:
                bad.append(f"{os.path.relpath(f, root)}: imports `{to}` ({m.group(1)}), which B-17's row for `{layer}` does not allow")
    return f"check_layering: {len(files)} module(s), {edges} import edge(s) between src/ files, {len(table)} table row(s)", bad


def check_error_budget(root):
    spec = _read(os.path.join(root, "meta", "specs", "SAFETY.md"))
    sec = spec[spec.index("## 3."):spec.index("## 4.")]
    names = set(re.findall(r"^\| `(E\w+)` \|", sec, re.M))
    s6 = sec[sec.index("**Rule S-6"):]
    nxt = s6.find("**Rule S-", 4)
    s6 = s6[:nxt] if nxt > 0 else s6
    allowed, prev = {}, set()
    for bullet in re.findall(r"^- (.+?)(?=^- |\Z)", s6, re.M | re.S):
        layers = re.findall(r"`nparse/(\w+)(?:/\*)?\.npk`", bullet)
        declared = set(re.findall(r"\*\*`(E\w+)`\*\*", bullet))
        if "additionally" in bullet:
            declared |= prev
        for lay in layers:
            allowed.setdefault(lay, set()).update(declared)
        prev = declared
    decl, sites, bad, files = {}, 0, [], _src_files(root)
    texts = {f: _blank(_read(f)) for f in files}
    for f, t in texts.items():
        mod = re.search(r"\bmod:(\w+)", t)
        for m in re.finditer(r"\berror:(\w+)", t):
            decl.setdefault(m.group(1), []).append((mod.group(1) if mod else "?", _layer(root, f), f))
    raised = set()
    for f, t in texts.items():
        mod = re.search(r"\bmod:(\w+)", t)
        for m in re.finditer(r"\bfail\s+([A-Za-z_]\w*)\s*;", t):
            sites += 1
            nm = m.group(1)
            here = [d for d in decl.get(nm, []) if d[2] == f]
            src = here[0] if here else (decl[nm][0] if nm in decl else ("prelude", "prelude", None))
            raised.add((src[0], nm, src[1]))
    for (mod, nm, lay) in sorted(raised):
        if nm not in names or nm not in allowed.get(lay, set()):
            bad.append(f"`{mod}.{nm}` is raised by a `fail` site, and SAFETY.md §3's table and S-6 allow "
                       f"{sorted(allowed.get(lay, set())) or 'no identity'} in the `{lay}` layer")
    keys = ", ".join(f"{m}.{n}" for m, n, _ in sorted(raised)) or "none"
    return (f"check_error_budget: {len(files)} module(s), {sum(len(v) for v in decl.values())} `error:` declaration(s), "
            f"{sites} `fail` site(s) naming one; identities raised, keyed by (module, name): {keys}"), bad


def _ints(text):
    for m in re.finditer(r"(?<![\w.])(0x[0-9a-fA-F_]+|0b[01_]+|[0-9][0-9_]*)(?:[iu](?:8|16|32|64))?(?![\w.])", text):
        s = m.group(1).replace("_", "")
        yield m.start(), int(s, 16) if s.startswith("0x") else int(s, 2) if s.startswith("0b") else int(s)


def check_constants_named(root):
    spec = _read(os.path.join(root, "meta", "specs", "SAFETY.md"))
    sec = spec[spec.index("## 7."):spec.index("## 8.")]
    unit = {"KiB": 1 << 10, "MiB": 1 << 20}
    bounds = {}
    for m in re.finditer(r"^\| `(NPARSE_\w+)` \| ([^|]+) \|", sec, re.M):
        v = m.group(2).strip()
        k = re.fullmatch(r"(\d+) (KiB|MiB)", v)
        p = re.fullmatch(r"2\^(\d+)(?:−1|-1)?", v)
        bounds[m.group(1)] = (int(k.group(1)) * unit[k.group(2)] if k else
                              (1 << int(p.group(1))) - (1 if v.endswith("1") and ("−" in v or "-" in v) else 0)
                              if p else int(v))
    values = set(bounds.values())
    bad, files, lits = [], _src_files(root), 0
    limits = os.path.join(root, "src", "core", "limits.npk")
    for f in files:
        t = _blank(_read(f))
        if f == limits:
            got = dict((n, int(v.replace("_", ""))) for n, v in
                       re.findall(r"\bfixed\s+int64:(NPARSE_\w+)\s*=\s*([0-9_]+)i64", t))
            for n, v in bounds.items():
                if got.get(n) != v:
                    bad.append(f"src/core/limits.npk: `{n}` is {got.get(n)}, SAFETY.md §7's table says {v}")
            for n in sorted(set(got) - set(bounds)):
                bad.append(f"src/core/limits.npk: `{n}` has no row in SAFETY.md §7's table")
            continue
        for pos, v in _ints(t):
            lits += 1
            if v in values:
                n = t[:pos].count("\n") + 1
                bad.append(f"{os.path.relpath(f, root)}:{n}: the literal {v} is a bound of SAFETY.md §7 -- name it from src/core/limits.npk")
    have = "present" if os.path.isfile(limits) else "absent until cycle 0.0.4"
    return (f"check_constants_named: {len(bounds)} bound(s) in SAFETY.md §7's table; {len(files)} module(s), {lits} integer "
            f"literal(s) outside limits.npk read; src/core/limits.npk {have}"), bad


def check_no_raw_accumulate(root):
    bad, files, read = [], _src_files(root), 0
    for f in files:
        rel = os.path.relpath(f, root)
        if not (rel.startswith(os.path.join("src", "scan") + os.sep) or rel.startswith(os.path.join("src", "format") + os.sep)):
            continue
        if os.path.basename(f) == "arith.npk":
            continue
        read += 1
        t = _blank(_read(f))
        for n, line in enumerate(t.split("\n"), 1):
            if re.search(r"(?<![-*/])\*(?![*/=])", line.replace("->", "  ")) and not re.match(r"\s*(//|/\*)", line):
                bad.append(f"{rel}:{n}: a `*` outside arith.npk -- an accumulation is range-checked first (PA-012)")
            m = re.search(r"\b(\w+)\s*=\s*\1\s*\+\s*([^;]+);", line)
            if m and not re.fullmatch(r"\s*\d+[iu]\d+\s*", m.group(2)):
                bad.append(f"{rel}:{n}: `{m.group(1)} = {m.group(1)} + ...` outside arith.npk (PA-012)")
    return f"check_no_raw_accumulate: {read} module(s) under src/scan/ and src/format/ outside arith.npk", bad


EXCEPTIONS = {}   # PA-117: empty, and empty at 1.0 -- "the grammar bounds the depth" is not a reason


def check_no_recursion(root):
    files = _src_files(root)
    body = {}
    for f in files:
        t = _blank(_read(f))
        for m in re.finditer(r"\bfunc:(\w+)(?:<[^>]*>)?\s*=[^{;]*\{", t):
            depth, k = 1, m.end()
            while k < len(t) and depth:
                depth += {"{": 1, "}": -1}.get(t[k], 0)
                k += 1
            body[m.group(1)] = t[m.end():k]
    calls = {fn: {c for c in re.findall(r"\b(\w+)\s*(?:::<[^>]*>)?\s*\(", b) if c in body} for fn, b in body.items()}
    bad, seen, state = [], set(), {}

    def walk(fn, path):
        state[fn] = 1
        for c in sorted(calls[fn]):
            if state.get(c) == 1:
                cyc = path[path.index(c):] + [c]
                key = frozenset(cyc)
                if key not in seen and not EXCEPTIONS.get(" -> ".join(cyc)):
                    seen.add(key)
                    bad.append("a call cycle: " + " -> ".join(cyc))
            elif not state.get(c):
                walk(c, path + [c])
        state[fn] = 2
    for fn in sorted(calls):
        if not state.get(fn):
            walk(fn, [fn])
    return (f"check_no_recursion: {len(files)} module(s), {len(body)} function(s), "
            f"{sum(len(v) for v in calls.values())} call edge(s) between them; exceptions: {len(EXCEPTIONS)}"), bad


def check_specs_current(root):
    defined = set()
    for f in sorted(os.listdir(os.path.join(root, "meta", "specs"))):
        if f.endswith(".md"):
            defined |= set(re.findall(r"\*\*Rule ([A-Z]-\d+[a-z]?)\b", _read(os.path.join(root, "meta", "specs", f))))
    cited, gone = set(), set()
    paths = _src_files(root) + sorted(os.path.join(root, "harness", f) for f in os.listdir(os.path.join(root, "harness"))
                                      if f.endswith(".py"))
    for f in paths:
        for c in re.findall(r"`?[A-Z]+\.md`? ([A-Z]-\d+[a-z]?)\b", _read(f)):
            cited.add(c)
            if c not in defined:
                gone.add(c)
    return (f"check_specs_current (reports only): {len(paths)} file(s), {len(cited)} rule id(s) cited beside a "
            f"specification's name, {len(gone)} that no specification defines{': ' + ' '.join(sorted(gone)) if gone else ''}"), []


ALL = [check_layering, check_error_budget, check_constants_named, check_no_raw_accumulate, check_no_recursion,
       check_specs_current]
LATER = [("check_no_owning_fields", "cycle 0.2, when `Event`, `Node`, `ParseError` and `Frame` exist"),
         ("check_codes_documented", "cycle 0.2"), ("check_failsafe_arms", "cycle 0.2"),
         ("check_corpus_provenance", "cycle 0.3")]
