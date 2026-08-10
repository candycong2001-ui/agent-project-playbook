---
name: multi-agent-routing
description: Decide whether and how a lead agent should delegate independent work. Use only when at least two bounded tasks can run independently with material benefit, or when the user explicitly requests multi-agent work. Do not trigger for small linear tasks or shared-state writes.
---

# Multi-Agent Routing

## Delegation gate

- `NO_DELEGATION` is a normal result. Keep work with the lead when it is small, linear, blocking, or expensive to verify.
- Delegate only independent tasks with clear ownership, useful parallelism, and cheap verification.
- Keep the user in one conversation; the lead owns scope, conflicts, integration, validation, and final delivery.

## Worker contract

1. State the bounded objective, owned files or surface, expected artifact, evidence required, and stop conditions.
2. Match capability and reasoning depth to the task; stronger reasoning does not grant broader permissions.
3. Workers do not create more workers or expand scope. Conflicts and higher-risk actions return to the lead.
4. The lead verifies material claims against current files, tests, or real output before adopting them.
5. Deployment, deletion, credentials, external writes, and final Git delivery remain under lead review and user authorization where required.
