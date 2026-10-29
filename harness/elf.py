#!/usr/bin/env python3
"""An ELF64 relocatable object's symbol table, read with `struct`.

The undefined-symbol scan is a BUILD STEP (`BUILD.md` B-2), and law here; resting law on a
fourth tool outside the manifest's pin, parsed out of text nothing checks, is the weaker
design, and the format is a few dozen lines of `struct`. It refuses anything that is not a
little-endian ELF64 object for x86-64 rather than guessing, because a mis-parsed symbol
table is a scan that reports clean. After `nitpick-regex`'s `harness/elf.py`.
"""
import struct

SHT_SYMTAB = 2
SHN_UNDEF = 0
STB_LOCAL = 0
STT_SECTION = 3
STT_FILE = 4


class ElfError(Exception):
    pass


class Obj:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            self.b = fh.read()
        b = self.b
        if len(b) < 64 or b[:4] != b"\x7fELF":
            raise ElfError(f"{path}: not an ELF file")
        if b[4] != 2 or b[5] != 1:
            raise ElfError(f"{path}: not little-endian ELF64")
        e_type, e_machine = struct.unpack_from("<HH", b, 16)
        if e_type != 1 or e_machine != 62:
            raise ElfError(f"{path}: e_type={e_type}, e_machine={e_machine}; not an x86-64 "
                           "relocatable object")
        (shoff,) = struct.unpack_from("<Q", b, 40)
        shentsize, shnum = struct.unpack_from("<HH", b, 58)
        if shentsize != 64:
            raise ElfError(f"{path}: e_shentsize={shentsize}, not 64")
        self.sections = []
        for i in range(shnum):
            (_, typ, _, _, soff, size, link, _, _, entsize) = struct.unpack_from(
                "<IIQQQQIIQQ", b, shoff + i * 64)
            self.sections.append((typ, soff, size, link, entsize))
        self.syms = []
        for typ, soff, size, link, entsize in self.sections:
            if typ != SHT_SYMTAB:
                continue
            if entsize != 24:
                raise ElfError(f"{path}: a symbol table entry of {entsize} bytes, not 24")
            for k in range(size // 24):
                nm, info, _, shndx, _, _ = struct.unpack_from("<IBBHQQ", b, soff + k * 24)
                self.syms.append((self._str(link, nm) if nm else "", info >> 4, info & 0xF, shndx))

    def _str(self, idx, off):
        base = self.sections[idx][1] + off
        return self.b[base:self.b.index(b"\0", base)].decode("utf-8", "replace")

    def undefined(self):
        """What `llvm-nm --undefined-only` prints: named, SHN_UNDEF, not local."""
        return sorted({n for n, bind, _, shndx in self.syms
                       if n and shndx == SHN_UNDEF and bind != STB_LOCAL})

    def defined(self):
        return sorted({n for n, _, typ, shndx in self.syms
                       if n and shndx != SHN_UNDEF and typ not in (STT_FILE, STT_SECTION)})

    def exported(self):
        """Every global symbol the object defines: all another object's reference can resolve to."""
        return sorted({n for n, bind, typ, shndx in self.syms
                       if n and shndx != SHN_UNDEF and bind != STB_LOCAL and typ not in (STT_FILE, STT_SECTION)})
