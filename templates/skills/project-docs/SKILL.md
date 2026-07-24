---
name: project-docs
description: Maintain this project's bounded BLUEPRINT, ARCHITECTURE, and CURRENT_HANDOFF documents and run Docs Lint. Use for substantial implementation or diagnosis, authorized handoff, scope or architecture changes, and documentation drift review.
---

# Project Docs

## Procedure

1. Read `docs/CURRENT_HANDOFF.md` at the start of substantial implementation or diagnosis.
2. Read only relevant sections of `docs/BLUEPRINT.md` and `docs/ARCHITECTURE.md`.
3. Verify documentation claims against current repository evidence.
4. During exploration or read-only review, report drift without editing documents unless authorized.
5. During authorized implementation, keep the current collaboration mode, project stage, one deliverable, one task frame, and one vertical slice in `CURRENT_HANDOFF.md`.
6. Replace stale state; never append a session diary.
7. Update `BLUEPRINT.md` only when product intent, users, scope, constraints, or acceptance change.
8. Update `ARCHITECTURE.md` only when components, boundaries, data flow, commands, deployment, rollback, or operational risks change.
9. Run `python3 .agents/skills/project-docs/scripts/docs_lint.py` before delivery.

## Truth and size discipline

- Current code, tests, configuration, command output, and user instruction outrank these documents.
- Keep BLUEPRINT at or below 160 lines.
- Keep ARCHITECTURE at or below 220 lines.
- Keep CURRENT_HANDOFF at or below 120 lines.
- Keep AGENTS at or below 180 lines.
