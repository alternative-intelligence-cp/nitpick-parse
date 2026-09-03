# `src/emit/` — the writers

One canonical writer per format. Every format that reads also writes (PA-060),
because the writer is half of the round-trip oracle that judges the reader.
Governed by `meta/specs/WRITER_MODEL.md`. Built alongside each format cycle,
starting at 0.5.
