#!/usr/bin/env python3
"""Cycle 0.0 -- every DECLARED NAME in `.npk` files, held to the compiler's keyword table: what the
compiler's landing 113 (DEF-235) refuses, `NITPICK-PARSE-001` at the declaration, where compiler
`7e91730`, the cycle's first pin, accepted some of them -- regex's field `stack` among them. The pin
`c9baa9e` carries 113, so its compiler refuses each, and this scanner is the plan's own count of them.

    python3 -B names.py <keywords.npk> <file>...            each declared name that is a keyword
    python3 -B names.py --count <keywords.npk> <file>...    and the count of declared names read

The keyword table is the pin's own `src/frontend/keywords.npk` (`git show <pin>:...`, byte-identical at
`7e91730` and `c9baa9e`, which the
caller writes to a file): every word its `keyword_kind_of` compares against. The rule, as landing
113's work states it in the compiler's `LEXICAL_REFERENCE.md` §4 note: "no keyword is a declared
name of ANY kind -- a function, a type, a trait, a module, an error, a unit, a rule, a macro, a
local or module binding, a parameter, a `for` binding, a field or a variant".

A DECLARED NAME, read here (comments and string literals blanked, as `shapes.py` blanks them):
  * the identifier IMMEDIATELY after a single `:` that follows a type or a declaring keyword with
    no space on either side -- `int64:n`, `Cursor->:c`, `fixed uint8[]:src`, `func:f`,
    `struct:S`, `enum:E`, `trait:T`, `mod:m`, `error:E`, `unit:u`, `rule:r`, `macro:m` -- which
    covers bindings, parameters, `for` bindings and fields; a struct literal's `field: value`
    and a bound's `T: Copy` carry a space and are not declarations; an `impl:` line's names are
    references and are not read;
  * each variant of an `enum:` body;
  * a `pick` arm's payload binding, `(E.V(x))`;
  * a generic parameter, `<T: Copy>` or `<T>`, after `func:`, `struct:` or `trait:`.
"""
import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from shapes import blank  # noqa: E402

DECLARING = r"(?:func|struct|enum|trait|mod|error|unit|rule|macro)"
_AFTER_COLON = re.compile(r"(?:[\w\]\)>?*]|->)(?<!:):(?!:)([A-Za-z_]\w*)")
_ENUM = re.compile(r"\benum:\w+\s*=\s*\{([^}]*)\}", re.S)
_ARM = re.compile(r"\(\s*[A-Za-z_][\w.]*\(\s*([A-Za-z_]\w*)\s*\)\s*\)")
_GENERIC = re.compile(r"\b" + DECLARING + r":\w+\s*<([^>]*)>")


def keywords(path):
    text = open(path, encoding="utf-8").read()
    return set(re.findall(r'string_eq\(text, "([^"]+)"\)', text))


def declared(path):
    """[(line, name)] for every declared name in the file."""
    with open(path, "rb") as fh:
        text = blank(fh.read().decode("utf-8", errors="replace"))
    out = []

    def at(pos, name):
        out.append((text[:pos].count("\n") + 1, name))

    for line_start, line in _lines(text):
        if re.match(r"\s*impl:", line):
            continue
        for m in _AFTER_COLON.finditer(line):
            at(line_start + m.start(1), m.group(1))
    for m in _ENUM.finditer(text):
        for v in re.finditer(r"(?:^|;)\s*([A-Za-z_]\w*)", m.group(1)):
            at(m.start(1) + v.start(1), v.group(1))
    for m in _ARM.finditer(text):
        at(m.start(1), m.group(1))
    for m in _GENERIC.finditer(text):
        for g in re.finditer(r"(?:^|,)\s*([A-Za-z_]\w*)", m.group(1)):
            at(m.start(1) + g.start(1), g.group(1))
    return sorted(set(out))


def _lines(text):
    pos = 0
    for line in text.split("\n"):
        yield pos, line
        pos += len(line) + 1


def main(argv):
    count = "--count" in argv
    args = [a for a in argv[1:] if a != "--count"]
    kw, files = keywords(args[0]), args[1:]
    total, hits = 0, []
    for f in files:
        names = declared(f)
        total += len(names)
        hits += [f"{f}:{ln} {nm}" for ln, nm in names if nm in kw]
    print(f"{len(files)} file(s), {total} declared name(s) read, {len(kw)} keywords; "
          f"keyword-named declarations: {len(hits)}" if count else
          f"keyword-named declarations: {len(hits)}")
    for h in hits:
        print("  " + h)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
