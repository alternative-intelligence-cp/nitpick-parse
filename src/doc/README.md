# `src/doc/` — the document model

`Document`: an arena-backed tree of POD nodes with a side string pool,
insertion-ordered maps, a duplicate-key policy, and the query API. Nodes own
nothing — an arena `get` returns a copy, so an owning field would make a node
unreadable. Governed by `meta/specs/VALUE_MODEL.md`. Built in cycle 0.4.
