#!/usr/bin/env python3
"""`nitpick.toml`, read the way `npkg` reads it -- `meta/specs/BUILD.md` B-1.

WHY A READER AND NOT `tomllib`. Python's `tomllib` accepts what `npkg`'s reader refuses, so a
manifest that worked here could be refused by the tool this harness retires into (PA-003).
The subset is the compiler's -- tables, `[[test]]` headers, strings, integers, booleans and
single-line arrays -- and a key the schema lacks is refused by name: a key nothing reads is
the next stale document (the compiler's D-204). After `nitpick-regex`'s `harness/manifest.py`.

THE SCHEMA IS THE COMPILER'S AT THE PIN: `npkg/manifest.npk`'s `schema_allows` at `7e91730`,
table for table and key for key, `[dependencies]` taking any key. Cycle 0.0.2's facts script
re-derives it from that function and compares (`0.0.2.md` §1.2).

THE STAGES are the compiler's vocabulary (`BUILD_REFERENCE.md` §7.1 at the pin) and this
library's two (`roundtrip`, `corpus`; `BUILD.md` §3). The compiler's rule is this runner's:
an entry it cannot honour is REFUSED BY NAME before anything runs, never skipped (`run.py`).
"""
import re


class ManifestError(Exception):
    pass


SCHEMA = {
    "project":      {"name", "version", "description", "authors", "target"},
    "build":        {"entry", "output", "opt-level"},
    "toolchain":    {"llvm", "triple", "datalayout",
                     "llc-flags", "llc-opt-flags", "opt-flags", "lld-flags"},
    "limits":       {"nofile"},
    "test":         {"name", "stage", "kind", "path", "paths", "recursive"},
    "verify":       {"z3", "z3-version", "z3-sha256", "z3-options"},
    "verify.nikos": {"domain"},
}
ANY_KEY = {"dependencies"}
KNOWN_STAGES = {"compile", "parse", "resolve", "check", "accept", "fixture", "program",
                "runtime", "verify", "cost", "explore", "roundtrip", "corpus"}
KNOWN_KINDS = {"positive", "negative", "diagnostic"}

_TABLE = re.compile(r'^\[([A-Za-z0-9_.-]+)\]$')
_ARRAY_TABLE = re.compile(r'^\[\[([A-Za-z0-9_.-]+)\]\]$')
_KEYVAL = re.compile(r'^([A-Za-z0-9_-]+)\s*=\s*(.*)$')


def _strip_comment(line):
    """A `#` outside a string starts a comment."""
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == "#" and not in_str:
            break
        out.append(ch)
    return "".join(out).strip()


def _split_top(inner):
    parts, cur, in_str = [], [], False
    for ch in inner:
        if ch == '"':
            in_str = not in_str
        if ch == "," and not in_str:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return [p for p in parts if p.strip()]


def _value(raw, where):
    raw = raw.strip()
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise ManifestError(f"{where}: a multi-line array -- the reader takes single-line "
                                "arrays only, as npkg's does")
        inner = raw[1:-1].strip()
        return [_value(p, where) for p in _split_top(inner)] if inner else []
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    try:
        return int(raw)
    except ValueError:
        raise ManifestError(f"{where}: {raw!r} is not a string, integer, boolean or "
                            "single-line array")


class Manifest:
    def __init__(self, tables, tests, path):
        self.tables, self.tests, self.path = tables, tests, path

    def need(self, table, key):
        if key not in self.tables.get(table, {}):
            raise ManifestError(f"{self.path}: [{table}] has no `{key}`")
        return self.tables[table][key]


def read(path):
    tables, tests, section, target = {}, [], None, None
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    for n, line in enumerate(lines, 1):
        text = _strip_comment(line)
        if not text:
            continue
        where = f"{path}:{n}"
        m = _ARRAY_TABLE.match(text)
        if m:
            section = m.group(1)
            if section != "test":
                raise ManifestError(f"{where}: [[{section}]] -- the only array table the "
                                    "schema has is [[test]]")
            target = {}
            tests.append(target)
            continue
        m = _TABLE.match(text)
        if m:
            section = m.group(1)
            if section == "test" or (section not in SCHEMA and section not in ANY_KEY):
                raise ManifestError(f"{where}: [{section}] is not a table the schema has")
            target = tables.setdefault(section, {})
            continue
        m = _KEYVAL.match(text)
        if not m:
            raise ManifestError(f"{where}: {text!r} is neither a table header nor `key = value`")
        if target is None:
            raise ManifestError(f"{where}: `{m.group(1)}` before any table header")
        key = m.group(1)
        if section not in ANY_KEY and key not in SCHEMA[section]:
            raise ManifestError(f"{where}: [{section}] has no key `{key}` in the schema "
                                f"(it has: {', '.join(sorted(SCHEMA[section]))})")
        if key in target:
            raise ManifestError(f"{where}: `{key}` given twice in [{section}]")
        target[key] = _value(m.group(2), where)
    seen = set()
    for i, t in enumerate(tests, 1):
        where = f"{path}: [[test]] #{i}"
        for k in ("name", "stage"):
            if k not in t:
                raise ManifestError(f"{where}: no `{k}`")
        if t["name"] in seen:
            raise ManifestError(f"{where}: `{t['name']}` is declared twice")
        seen.add(t["name"])
        if t["stage"] not in KNOWN_STAGES:
            raise ManifestError(f"{where} ({t['name']}): stage `{t['stage']}` is not a stage")
        if "kind" in t and t["kind"] not in KNOWN_KINDS:
            raise ManifestError(f"{where} ({t['name']}): kind `{t['kind']}` is not a kind")
        if ("path" in t) == ("paths" in t):
            raise ManifestError(f"{where} ({t['name']}): exactly one of `path` and `paths`")
    return Manifest(tables, tests, path)


def paths_of(t):
    """`path` names a directory; `paths` a list of them."""
    return list(t["paths"]) if "paths" in t else [t["path"]]
