# `src/core/` — storage primitives

`Vec<T>`, `Bytes`, `SmallMap<K,V>`, and `limits.npk` — every named bound in the
library, in one file, because a bound scattered across call sites is a bound
nobody can audit. Depends on nothing. Governed by `meta/specs/BUILD.md` §5.
Built in cycle 0.0.4.
