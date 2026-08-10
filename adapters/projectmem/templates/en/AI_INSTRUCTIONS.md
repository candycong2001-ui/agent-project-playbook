# Projectmem Working Rules

Projectmem is this repository's cold memory, not its source of truth.

## Read boundary

- Start with current files, tests, configuration, and real command output.
- Query projectmem only for prior decisions, repeated failures, fragile paths, or explicit historical questions.
- Treat memory results as clues until current repository evidence verifies them.

## Write boundary

- Do not save activity streams, commit summaries, watcher churn, chat logs, or raw tool output.
- A commit is not a decision.
- Save a durable decision only when its choice, reason, scope, and evidence are clear.
- Keep uncertain observations as candidates; do not promote them automatically.
- Never store credentials, tokens, cookies, personal data, or private raw logs.

## Automation defaults

- Watcher, Git hooks, history backfill, global inheritance, and MCP setup stay off.
- Keep generated runtime files out of Git.
- Keep the summary bounded and run Docs Lint before substantial handoff work.
