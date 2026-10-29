#!/usr/bin/env python3
"""The harness's one reading of `.npk` source text (PA-117): a file read as BYTES, `\\n` the only line end as in
the compiler's lexer, and `blank()` replacing comments and string and character literals by spaces, line
structure kept -- so a check reading code is not fooled by a word in a comment, and every line number it reports is
the file's. The tree checks (`treecheck.py`) and the parse sweep's reader use it.
"""
import re


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


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
