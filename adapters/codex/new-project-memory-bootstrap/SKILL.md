---
name: new-project-memory-bootstrap
description: Initialize the Agent Project Playbook, bounded project documents, local Skills, and optional quiet projectmem when the user explicitly starts a new project or asks for meminit, AGENTS, BLUEPRINT, ARCHITECTURE, CURRENT_HANDOFF, or Docs Lint setup.
---

# New Project Memory Bootstrap

1. Do not initialize while the user is only exploring an idea.
2. Inspect the selected project for an existing `AGENTS.md` or equivalent document system.
3. Use `simple` unless current evidence shows a real runtime, shared state, real users, credentials, or external writes; then recommend `production`.
4. Run `meminit <project-path> <project-name>` as a dry-run; do not make the user remember this command.
5. Explain existing-file conflicts instead of installing a second rules system.
6. If the user's original request already explicitly authorizes installation and the dry-run has no conflict, apply without asking again. Otherwise ask once before `--apply`.
7. Activate the generated blueprint, architecture, handoff, and project map from current evidence.
8. Run the installed Docs Lint before the first substantial handoff.

The standard command installs Playbook Core without external dependencies. Add `--with-projectmem` only when the user explicitly wants the optional cold-memory adapter and `pjm` is available. The adapter keeps watcher, Git hooks, history backfill, global inheritance, and MCP setup off.

Never import another project's memory, overwrite existing project files, or invent project facts.
