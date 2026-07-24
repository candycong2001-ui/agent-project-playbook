---
name: agent-project-bootstrap
description: Bootstrap the Agent Project Playbook into a user-selected project with a dry-run first. Use when the user explicitly asks to initialize project collaboration rules, BLUEPRINT, ARCHITECTURE, CURRENT_HANDOFF, or the project-docs skill.
---

# Agent Project Bootstrap

## Procedure

1. Confirm the target project root, project name, and document locale (`en` or `zh-CN`).
2. Run `python3 scripts/init_project.py <path> --project-name <name> --locale <locale>` from this repository.
3. Review the dry-run report with the user.
4. If the target already has equivalent rules or documents, stop and prepare a manual merge plan.
5. Apply only after explicit confirmation with the same locale and `--apply`.
6. Activate the generated documents using current repository evidence, keeping collaboration mode and project lifecycle stage as separate fields.
7. Mark unverified commands, deployment paths, and risks instead of guessing.
8. Run the installed Docs Lint before handing implementation work back.

## Safety

- Never overwrite existing project files.
- Never import another project's memory or status.
- Never store secrets / 密钥, tokens, cookies, personal data, or private logs.
- Never configure external memory services or global Agent settings from this skill.
- Current repository evidence outranks every generated placeholder.
