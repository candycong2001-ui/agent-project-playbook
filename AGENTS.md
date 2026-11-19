# Agent Project Playbook Working Agreement

## Truth order

- Current user decisions establish goals, scope, and authorization.
- Current files, configuration, tests, and command output establish what is implemented, verified, and running.
- Use the published protocol and historical discussion to locate evidence and prior decisions.

## Repository purpose

- Keep the core collaboration protocol model-agnostic.
- Keep platform-specific behavior in explicit adapters.
- Never publish personal paths, credentials, project memories, private logs, or another project's state.
- Treat examples as examples, not inherited project facts.

## Change rhythm

1. Identify the protocol problem and observable failure it addresses.
2. Update the canonical protocol before derived templates.
3. Keep the initializer non-destructive and dry-run by default.
4. Update tests for every installation or required-heading change.
5. Run every validation command listed in `CONTRIBUTING.md` before delivery.

## Scope discipline

- One independently verifiable protocol slice per change.
- Park unrelated adapters, visual polish, and distribution work.
- Do not claim compatibility with an Agent platform until its adapter has been tested there.
- Keep public documentation concise and free of project-specific history.

## Manager mode

- The user interacts only with the lead Agent; subagents do not take over the conversation or declare final completion.
- Keep the user-selected lead model for orchestration, architecture, conflict resolution, high-risk review, and replanning.
- For permitted delegation, choose currently available capabilities and reasoning depth against task and cost requirements. Inheritance is valid when its known configuration meets those requirements; do not require an explicit override solely to avoid inheritance.
- Escalated judgment returns to the lead Agent; model choice does not expand delegation or external-write authority.
- Treat `NO_DELEGATION` as a valid route. Delegate only when work is independent, materially beneficial, non-blocking, and cheaply verifiable.
- Keep role, model tier, reasoning effort, and permission scope separate; stronger reasoning never grants wider authority.
- Use the host's available capacity and leave room for verification, review, and recovery; on creation or access failure, check worker state and take over or replan.
- Give writing Workers exclusive ownership, forbid descendant delegation, and archive only outputs the lead has verified and adopted.
- Workers that exceed scope or risk return `ESCALATE_TO_MAIN` with evidence instead of expanding the task.
- Verify material subagent claims against current repository evidence before integration or delivery.

## Release

- Use semantic versions.
- Record user-visible changes in GitHub Releases.
- A release must state validation evidence and known compatibility limits.
