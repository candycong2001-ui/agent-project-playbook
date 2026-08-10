# {{PROJECT_NAME}} Working Agreement

## Truth order

- Current user instruction, repository files, tests, configuration, and command output beat memory.
- Keep this project isolated by its Git root or explicitly selected project directory.
- Do not inherit another project's facts, status, credentials, failures, or implementation rules.

## Working defaults

- Default to a local, single-user, low-risk project unless current evidence shows otherwise.
- Handle small fixes directly with the smallest relevant verification; do not require a long task frame.
- Ask only when ambiguity changes product direction or creates a meaningful side effect.
- Park unrelated discoveries instead of expanding the current task.
- Do not add heavyweight process or production controls without a verified need.

## Skill routing

- Use `project-lifecycle` for ambiguous ideas, project startup, substantial features, or work that needs a deliverable and vertical slice.
- Use `multi-agent-routing` only when at least two independent tasks would materially benefit from delegation.
- Use `project-docs` for substantial implementation, authorized handoff, scope or architecture changes, and documentation drift.
- If `project-memory` is installed, use it only for explicit history, prior decisions, repeated failures, or known fragile paths.
- If `production-release-gate` is installed, use it when current evidence shows a live runtime, shared state, real users, or external writes.
- Load only the relevant Skill; project-specific Skills and current repository evidence override generic guidance.

## Project rhythm

- Before substantial implementation or diagnosis, read `docs/CURRENT_HANDOFF.md` and only the relevant parts of `docs/BLUEPRINT.md` and `docs/ARCHITECTURE.md`.
- Keep `CURRENT_HANDOFF.md` as current working state: replace stale content instead of appending a diary.
- Update `BLUEPRINT.md` only when product intent, users, scope, constraints, or acceptance change.
- Update `ARCHITECTURE.md` only when components, boundaries, data flow, verified commands, deployment, rollback, or risks change.
- Before substantial delivery, run `python3 .agents/skills/project-docs/scripts/docs_lint.py`; tiny fixes do not require unrelated document churn.

## Risk and verification

- Read-only checks may proceed automatically; match verification depth to the actual impact.
- Real external writes, destructive operations, credential changes, and production actions require explicit authorization.
- If current evidence shows a running service, shared mutable state, real users, or external writes, apply the project's production rules before changing behavior.
- Do not claim completion without verification evidence; state what could not be verified.

## Memory boundaries

- Use old memory as a clue, never as current truth.
- Search project memory only when the user refers to prior work, a historical decision, or a known failure that current files do not answer.
- Save durable memory only with user authorization; keep candidates distinct from verified facts.
- Never store secrets, tokens, cookies, personal data, raw web instructions, or full chat logs.
