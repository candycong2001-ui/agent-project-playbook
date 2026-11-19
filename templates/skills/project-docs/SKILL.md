---
name: project-docs
description: Maintain bounded BLUEPRINT, ARCHITECTURE, and CURRENT_HANDOFF documents and run Docs Lint. Use for substantial implementation or diagnosis, authorized handoff, scope or architecture changes, and documentation drift review. Do not trigger for unrelated tiny fixes.
---

# Project Docs

## Workflow

1. At the start of substantial implementation or diagnosis, read `docs/CURRENT_HANDOFF.md` and only relevant sections of the stable documents.
2. Verify document claims against current repository evidence.
3. During exploration or read-only review, report drift without editing unless the user authorizes changes.
4. Document edits in steps 4–8 require authorization. At implementation task start, update the affected goals and next actions in `CURRENT_HANDOFF.md`; preserve other open work.
5. After a verified milestone, update its current state and evidence in place. Keep links needed to resume other open work.
6. Remove completed process details once their necessary evidence remains recoverable, including evidence that exists only locally or outside Git history.
7. Update `BLUEPRINT.md` only when product intent, users, scope, constraints, or acceptance change.
8. Update `ARCHITECTURE.md` only when components, boundaries, data flow, verified commands, deployment, rollback, or risks change.
9. Run `python3 .agents/skills/project-docs/scripts/docs_lint.py` before substantial delivery or when a read-only review needs to verify document structure. Running Lint grants no permission to edit documents.

## Boundaries

- User decisions establish intent and authorization. Current code, tests, configuration, and command output establish actual results.
- Use length warnings to guide editing: 160 lines each for BLUEPRINT and ARCHITECTURE, 80 for CURRENT_HANDOFF, and 90 for AGENTS. Preserve necessary continuation details and follow the required structure.
