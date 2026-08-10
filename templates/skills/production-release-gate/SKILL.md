---
name: production-release-gate
description: Route changes for a project with a verified live runtime, shared mutable state, real users, credentials, or external writes. Use when current evidence shows production impact or the user asks to deploy, restart, migrate, or roll back. Do not trigger for a simple local project or documentation-only work with no runtime effect.
---

# Production Release Gate

## Establish the real boundary

1. Read the project's current operations and architecture instructions; do not import commands from another project.
2. Inspect the current branch, working tree, running surface, active jobs, persistent state, and external-write boundary only as relevant.
3. Use `python3 .agents/skills/production-release-gate/scripts/project_safety.py inspect .` when Git worktree separation is part of this project's workflow.
4. Let current evidence raise the risk level. The user does not need to say a special phrase.

## Route by affected surface

| Change | Default production action |
| --- | --- |
| Documentation only | Merge or publish documentation; no runtime action |
| Frontend/static assets | Update the production source and rebuild assets; do not restart an unrelated backend |
| Backend/API | Update the production source and restart only the affected service |
| Worker/report/scheduled job | Restart only the affected resident process; an idle scheduled job can wait for its next run |
| Dependency | Update the project-defined runtime environment and restart only affected processes |
| State structure, migration, or external write | Check active work, prepare the relevant backup or rollback path, validate narrowly, then obtain explicit authorization |

Project operations documentation overrides these defaults. Do not invent a backup, restart, or environment layer that the project does not use.

## Delivery gate

- `main` is reviewed source, not a deployment event.
- Before changing a live runtime, show the affected surface, current evidence, validation, expected impact, and rollback action.
- Deployment, process restart with user impact, data migration, credential change, and real external writes require explicit authorization.
- After the action, run the project-defined health check and report the actual result.
