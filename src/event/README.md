# `src/event/` — the event contract

The format-neutral event vocabulary, `Step` (`Ev` / `Fault` / `Done`), the
`Format` trait every plugin implements, the pull driver, and the explicit depth
stack. This is the interface the whole library is built around, and it is what
a third-party format implements. Governed by `meta/specs/EVENT_MODEL.md` and
`meta/specs/PLUGIN_MODEL.md`. Built in cycle 0.2.
