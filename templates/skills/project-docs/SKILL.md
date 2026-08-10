---
name: project-docs
description: Maintain bounded BLUEPRINT, ARCHITECTURE, and CURRENT_HANDOFF documents and run Docs Lint. Use for substantial implementation or diagnosis, authorized handoff, scope or architecture changes, and documentation drift review. Do not trigger for unrelated tiny fixes.
---

# Project Docs

## Workflow

1. At the start of substantial implementation or diagnosis, read `docs/CURRENT_HANDOFF.md` and only relevant sections of the stable documents.
2. Verify document claims against current repository evidence.
3. During exploration or read-only review, report drift without editing unless the user authorizes changes.
4. At task start, replace the current goal and next action in `CURRENT_HANDOFF.md`.
5. After a verified milestone, replace current state and verification evidence; do not append a timeline.
6. Before handoff, remove completed process details and leave one continuation-ready state.
7. Update `BLUEPRINT.md` only when product intent, users, scope, constraints, or acceptance change.
8. Update `ARCHITECTURE.md` only when components, boundaries, data flow, verified commands, deployment, rollback, or risks change.
9. Before substantial delivery, run `python3 .agents/skills/project-docs/scripts/docs_lint.py`.

## Boundaries

- Current code, tests, configuration, command output, and user instruction outrank these documents.
- Keep BLUEPRINT at or below 160 lines.
- Keep ARCHITECTURE at or below 160 lines.
- Keep CURRENT_HANDOFF at or below 80 lines.
- Keep AGENTS at or below 90 lines.
- Git stores history. CURRENT_HANDOFF stores only the latest working state.
