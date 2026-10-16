#!/usr/bin/env python3
"""Cycle 0.0 -- read `.npk` files the way the compiler does (bytes; `\\n` the only line end; comments and string
literals blanked) and count the shapes a plan must not write: those whose answer moved between compiler `7e91730`,
the cycle's first pin, and the landings its pin `c9baa9e` carries (the cycle README's landing list), and those a
pin is silent on.

    python3 -B shapes.py <file>...           one line per shape: its count over all the files
    python3 -B shapes.py --sites <file>...   and every site, `<file>:<line>`, beside it

The shapes, each with the landing or the row that moves it:
  a valued enum variant          106 (D-342 R1: an enum values every variant or none)
  a macro                        106 (D-343)
  a held `@`/`$$` binding        105 (DEF-159: a store through a held `@x` after `move(x)`)
  `give`, `fall`, `frac`          111 (DEF-233, DEF-238)
  a `NIL`-typed field            112 (DEF-232)
  `opaque`                       113 (DEF-236 (e))
  an attribute name              113 (DEF-236 (d): an unknown one ignored at `7e91730`, `DERIVE-007` at `c9baa9e`) -- listed by name
  a builtin named, not called    107 (DEF-243)
  `exit` operands, by form       104 (DEF-249: the operand is held to `int32`)
  `#wild_slice`                  the read-only view rule (no untied view of a managed header, D-341)
  a plain `uint8[]`              the read-only view rule -- listed, because a probe may need one on purpose
  `stack` as a name              `PLAYBOOK.md` §10 (a memory qualifier: PARSE-002 far from the cause)
  `.is_error ||` and its mirror  `PLAYBOOK.md` §2 (`if (a.is_error || b.is_error)` clears neither taint)
  a `failsafe` whose first statement is not its `pick`   109 (DEF-224 finds a nested pick; `7e91730` did not)
  a trait default calling a sibling on `self`   118 (DEF-254: it never links before) -- added by cycle 0.0.2's
                                 plan, with its own planted control, `shapes_planted_later.txt`
"""
import re
import sys

BUILTINS = ["alloc", "ralloc", "dalloc", "mcpy", "buffer_new", "string_concat", "int_to_string", "string_bytes",
            "string_from_bytes", "arena_make", "to_cstring", "sys", "discard"]


def blank(src):
    """Comments and string/char literals replaced by spaces, line structure kept."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j])); i = j
        elif c == '"' or c == "'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(c + " " * max(0, j - i - 2) + (c if j - i >= 2 else "")); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def scan(path):
    with open(path, "rb") as fh:
        raw = fh.read().decode("utf-8", errors="replace")
    text = blank(raw)
    lines = text.split("\n")
    found = {}

    def hit(shape, line_no):
        found.setdefault(shape, []).append("%s:%d" % (path, line_no))

    in_enum = 0
    for k, line in enumerate(lines, 1):
        if re.search(r"\benum:\w+", line):
            in_enum = 1
        if in_enum and re.search(r"\b[A-Z]\w*\s*=\s*-?\d", line):
            hit("a valued enum variant", k)
        if in_enum and "}" in line:
            in_enum = 0
        if re.search(r"\bmacro\b", line):
            hit("a macro", k)
        if re.search(r"->:\w+\s*=\s*(@|\$\$[im])", line):
            hit("a held `@`/`$$` binding", k)
        for w in ("give", "fall", "frac"):
            if re.search(r"\b%s\b" % w, line):
                hit("`%s`" % w, k)
        if re.search(r"\bNIL:\w+\s*;", line):
            hit("a `NIL`-typed field", k)
        if re.search(r"\bopaque\b", line):
            hit("`opaque`", k)
        for a in re.findall(r"#\[\s*(\w+)\s*\(([^)]*)\)", line):
            for name in [a[0]] + [x.strip() for x in a[1].split(",") if x.strip()]:
                hit("attribute %s" % name, k)
        for b in BUILTINS:
            for m in re.finditer(r"\b%s\b" % b, line):
                rest = line[m.end():]
                if not re.match(r"\s*(\(|::<)", rest):
                    hit("a builtin named, not called", k)
        for m in re.finditer(r"\bexit\s+([^;]+);", line):
            op = m.group(1).strip()
            if re.fullmatch(r"\d+i32", op):
                kind = "an int32 literal"
            elif re.fullmatch(r"\(.*=>!?\s*int32\)", op):
                kind = "a cast to int32"
            else:
                kind = "`%s`" % op
            hit("exit operand: %s" % kind, k)
        if "#wild_slice" in line:
            hit("`#wild_slice`", k)
        for m in re.finditer(r"(?<!fixed )\buint8\[\]", line):
            hit("a plain `uint8[]`", k)
        if re.search(r"\bstack\b", line):
            hit("`stack` as a name", k)
        if re.search(r"\.is_error\s*\|\||\|\|\s*!?\s*\w+\.is_error", line):
            hit("`.is_error ||`", k)
    for m in re.finditer(r"func:failsafe\s*=\s*int32\(Error:\w+\)\s*\{\s*(\S+)", text):
        if m.group(1) != "pick":
            hit("a `failsafe` not opening with its `pick`", text[:m.start()].count("\n") + 1)
    for m in re.finditer(r"\btrait:\w+[^=]*=\s*\{", text):
        body = _braced(text, m.end() - 1)
        for f in re.finditer(r"\bfunc:\w+", body):
            k = f.end()
            while k < len(body) and body[k] not in "{;":
                k += 1
            if k < len(body) and body[k] == "{" and re.search(r"\bself\.\w+\s*\(", _braced(body, k)):
                hit("a trait default calling a sibling on `self`", text[:m.end() + f.start()].count("\n") + 1)
    return found


def _braced(text, at):
    """The text inside the brace at `at` and its match."""
    depth, k = 0, at
    while k < len(text):
        depth += {"{": 1, "}": -1}.get(text[k], 0)
        if depth == 0:
            return text[at + 1:k]
        k += 1
    return text[at + 1:]


def main(argv):
    sites = "--sites" in argv
    files = [a for a in argv[1:] if a != "--sites"]
    total = {}
    for f in files:
        for shape, where in scan(f).items():
            total.setdefault(shape, []).extend(where)
    print("%d file(s) read" % len(files))
    for shape in sorted(total):
        print("  %s: %d%s" % (shape, len(total[shape]), ("  " + " ".join(total[shape])) if sites else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
