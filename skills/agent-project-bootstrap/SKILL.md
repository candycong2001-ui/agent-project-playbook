---
name: agent-project-bootstrap
description: Bootstrap the Agent Project Playbook into a user-selected project with a dry-run first. Use when the user explicitly asks to initialize project collaboration rules, BLUEPRINT, ARCHITECTURE, CURRENT_HANDOFF, or the project-local lifecycle, multi-agent, and docs skills.
---

# Agent Project Bootstrap

## Procedure

1. Confirm the target project root, project name, and document locale (`en` or `zh-CN`).
2. Use the `simple` profile unless current repository evidence shows a live runtime, shared state, real users, credentials, or external writes; then recommend `production`.
3. Run `bin/meminit <path> <name>` from this repository. Add `--production` only for the production profile, or `--without-projectmem` when the optional cold-memory adapter is not wanted.
4. Review the dry-run report with the user.
5. If the target already has Playbook files, run the same command with `--upgrade` and prepare a manual merge plan.
6. Apply a new installation only after explicit confirmation with the same locale, profile, and `--apply`.
7. Activate the generated documents using current repository evidence and keep `CURRENT_HANDOFF.md` limited to one current state.
8. Mark unverified commands, runtime side effects, and risks instead of guessing.
9. Run the installed Docs Lint before handing substantial implementation work back.

## Safety

- Never overwrite existing project files.
- Never import another project's memory or status.
- Never store secrets / 密钥, tokens, cookies, personal data, or private logs.
- Never configure MCP, cross-project memory, background watchers, or global Agent settings from this skill.
- `--upgrade` is read-only; never combine it with `--apply` or overwrite project customization.
- The default simple install does not include production safety tooling.
- The optional projectmem adapter keeps hooks, watcher, history backfill, global inheritance, and automatic capture off.
- Current repository evidence outranks every generated placeholder.
