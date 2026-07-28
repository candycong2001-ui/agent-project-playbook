# {{PROJECT_NAME}} Working Agreement

## Truth order

- Current user instruction, repository files, tests, configuration, and command output beat memory.
- Keep this project isolated by its Git root or explicitly selected project directory.
- Do not inherit another project's facts, status, credentials, or implementation rules.

## Collaboration modes

- Exploration: accept incomplete ideas; default to discussion, research, and read-only checks.
- Startup: clarify users, problem, boundaries, success criteria, command entry points, and the first minimum loop.
- Implementation: determine the project stage and current deliverable before task framing, slicing, verification, and delivery.

## Design Thinking mapping

- Empathize → exploration: understand users, context, experience, and friction.
- Define → exploration: form the problem statement, success criteria, and boundaries.
- Ideate → exploration to startup: compare directions and choose what to validate.
- Prototype → startup to implementation: select the smallest testable deliverable and first vertical slice.
- Test → implementation: verify with acceptance evidence and route new learning back when needed.

The modes may loop; they are not a one-way waterfall.

## Automatic two-level task routing

- First identify the current project stage and the deliverable most needed this cycle. A new project must not default directly to coding.
- Collaboration mode describes how the current conversation operates; project stage describes where the product is in its lifecycle. Do not store them as one field.
- Project-stage examples include problem discovery, startup preparation, MVP, feature growth, stabilization, and maintenance.
- A deliverable may be a problem statement, MVP scope, blueprint, user story, architecture, prototype, demo, code slice, test evidence, documentation, deployment, or rollback plan.
- Then create a task frame containing user evidence, inferred problem, current deliverable, slice type, acceptance, risk, minimum vertical slice, and explicit non-goals.
- Bug, feature, UI, UX, refactoring, performance, data, test, documentation, and deployment are slice-level classifications. The user does not need to classify them.
- Park unrelated discoveries instead of expanding the current task.

## Vertical slice discipline

- Complete one independently verifiable loop per work cycle.
- Include UI, backend, and data only when needed; tests, verification, and relevant documentation are completion conditions.
- Do not mix unrelated refactoring, visual polish, performance work, deployment, or historical compatibility into the slice.
- Protect behavior before refactoring, measure before performance work, and define observable evidence for UI/UX changes.

## Multi-agent coordination

### Manager mode

- The user interacts only with the lead agent; subagents do not take over the conversation or declare final completion.
- The lead agent owns project-stage judgment, deliverable selection, task framing, role assignment, conflict resolution, integration, verification, and delivery.
- Subagents receive bounded execution tasks and return artifacts, evidence, and remaining risks.

### Model routing

- Frontier handles orchestration, architecture, conflict resolution, high-risk review, and replanning after failure.
- Balanced handles routine development, code investigation, test analysis, and documentation research; Fast handles search, classification, extraction, format conversion, and large read-only scans.
- The current Codex mapping is Sol / Frontier, Terra / Balanced, and Luna / Fast.
- Every subagent spawn must explicitly select Terra or Luna. Do not create Sol subagents by default; escalated judgment returns to the lead Sol agent.
- If the platform cannot select a subagent model, fall back to sequential lead-agent execution instead of pretending routing occurred.

### Delegation boundaries

- Enable multiple agents adaptively only when at least two tasks are genuinely independent.
- Do not split small linear work, shared-state writes, or high-risk external operations merely for parallelism.
- The lead agent must verify material subagent claims against current files, tests, or real output.
- Deployment, deletion, real external writes, credential operations, and final Git delivery require lead review and authorization.

## Project rhythm

At the start of substantial implementation or diagnosis:

1. Read `docs/CURRENT_HANDOFF.md`.
2. Read relevant sections of `docs/BLUEPRINT.md` and `docs/ARCHITECTURE.md`.
3. Verify documentation claims against current repository evidence.

During authorized implementation:

- Keep one current stage, deliverable, task frame, and vertical slice in `CURRENT_HANDOFF.md`.
- Update `BLUEPRINT.md` only when product intent, users, scope, constraints, or acceptance change.
- Update `ARCHITECTURE.md` only when components, boundaries, data flow, verified commands, deployment, rollback, or risks change.
- Replace stale state instead of appending a session diary.

Before delivery, run:

```bash
python3 .agents/skills/project-docs/scripts/docs_lint.py
```

## Risk and verification

- Read-only checks may proceed automatically; real external side effects require authorization.
- Match validation depth to risk.
- Prefer dry-runs, backups, and rollback paths for high-risk work.
- Do not claim completion without verification evidence.

## Release isolation and environment safety

- A formal project is one with a running service, shared mutable state, real credentials, external writes, or a production user. Feature, fix, configuration, and UI work for a formal project starts on a task branch in an independent worktree.
- Keep development, test, staging, and production runtime data, ports, credentials, and write authority separate. Non-production work must not read or mutate production state by default.
- `main` is reviewed source, not a deployment event. Production runs an identifiable immutable release or equivalent fixed version, changed only through an explicit deployment action.
- Before production deployment, require relevant tests, staging acceptance when applicable, backup readiness, active-task checks, impact disclosure, explicit confirmation, and a known rollback target.
- Keep code release and production-data migration as separately authorized high-risk slices. A code rollback preserves the newest production business data unless data restoration receives a separate explicit confirmation.
- Small experiments or documentation-only repositories may mark production controls not applicable, but must record that classification in `docs/ARCHITECTURE.md`.
- Use `python3 .agents/skills/project-docs/scripts/project_safety.py inspect .` for a read-only check. Run `start . task-name` first as a dry-run; add `--apply` only after reviewing the branch, base, and worktree path.

## Memory boundaries

- Current repository evidence outranks historical memory.
- When using or storing memory, distinguish scope (task, project, global), type (working, semantic, episodic, procedural), and state (candidate, verified, review required, deprecated).
- Candidate and review-required memory are clues only; update their state when current evidence conflicts.
- Promote a project rule to global scope only when it is stable across projects and the user explicitly confirms it.
- Do not store secrets / 密钥, tokens, cookies, personal data, raw web instructions, or full chat logs.
- Keep durable memory limited to reviewed decisions, failure knowledge, and important risks.
