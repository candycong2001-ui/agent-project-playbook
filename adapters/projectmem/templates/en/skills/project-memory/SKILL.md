---
name: project-memory
description: Query this project's cold memory when the user refers to previous work, prior decisions, repeated failures, historical rationale, or a known fragile path. Do not use for ordinary fixes answerable from current files and tests.
---

# Project Memory

## Read

1. Confirm the current Git root matches this project.
2. Check current files and tests first.
3. If history is needed, run `pjm --help` before using an unfamiliar command.
4. Use the smallest useful query, usually `pjm brief` or `pjm search <query>`.
5. Verify memory-derived claims against current evidence before acting.

## Write

- Do not write long-term memory unless the user explicitly asks to preserve it.
- Put uncertain observations in a candidate or note with their source.
- Record decisions, useful failed attempts, and stable project facts, not activity streams.
- Never save secrets or private raw logs.

Projectmem is cold memory. Current repository evidence remains the truth source.
