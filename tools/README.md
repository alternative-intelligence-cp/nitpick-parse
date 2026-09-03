# `tools/` — instruments

`fuzz.py` (the decoder fuzzer and its four invariants), `vendor_corpus.py` (the
conformance-corpus vendoring script, which records the upstream commit it took
and refuses to run during a build). Nothing here runs in a build: a build needs
the compiler and nothing else.
