---
name: reference-first-project-scout
description: Check mature methods and reusable implementations when a new project direction or important architecture, component, or methodology choice is still open. Start with a quick reference pass. Skip narrow fixes, unchanged approved choices, and requests only to install project scaffolding.
---

# Reference First Project Scout

Help choose what to build or borrow before committing to an open design choice.
The outcome is a recommendation with evidence and one small fit check, not a new
project lifecycle, a compulsory research report, or permission to implement.

## When to use

- Use proactively for an undecided new project or a consequential open choice.
- Use when the user explicitly asks for reference research or build-versus-reuse advice.
- Skip small fixes, cosmetic edits, one-off scripts, learning exercises, and emergency recovery.
- Skip an approved choice whose requirements have not changed, or a request only to install governance.
- When a previous pass still applies, use its conclusion; investigate only changed assumptions.

## Default: a quick pass

1. Take the current problem, constraints, and success criteria from the user or existing project context.
   Do not repeat lifecycle planning. If the choice is unclear, identify the one uncertainty that matters.
2. Check relevant current-project code, dependencies, tests, and explicitly reusable shared Skills or templates.
   Do not enumerate the user's other repositories, private knowledge bases, cold memory, or past sessions.
   Inspect another project only when the user has named it as a reference or authorized that scope.
   Project memory still follows its own trigger rules; research is not a new memory-reading permission.
3. Select the evidence lanes that can answer the uncertainty: mature methods or standards,
   implementations or components, empirical cases, and current internal assets.
   They are alternatives to explore, not four mandatory deliverables.
4. Search relevant primary sources with generic capability terms, leaving private details out of queries.
   GitHub is useful for software reuse, not mandatory for every question. Do not fill a candidate quota.
   Follow an explicit no-browsing request; disclose unavailable sources without blocking unrelated work.
5. Inspect enough evidence for the recommendation. For a serious code candidate, inspect the relevant
   execution path, tests, dependencies, and license when available; README claims alone are not verification.
   A closed-source product can still be compared, but label its claims as documented, not source-verified.
6. Give the preferred route, what not to copy, the important uncertainty, and one representative fit check.
   Stop once further searching would not change the decision. Do not turn a short check into a survey.

## Keep two decisions separate

- Method: adopt, adapt, use as a comparison, or do not adopt. Use this only when a method matters.
  Explain the relevant assumption, how it maps to this project, and the part that does not transfer.
- Implementation: reuse current code, adopt or compose a component, borrow a pattern, or build fresh.
  Borrowing a method does not require importing its platform. Finding no suitable reuse is valid.
- Separate documented claims, source-inspected behavior, and actual runtime results.
  If a check was not performed, say so; do not label a promising candidate as proven.

## Go deeper only when it matters

For a consequential long-lived choice, actual high risk, or an explicit deep review,
read [the deeper review guide](references/deeper-review.md).
Choose only the dimensions capable of changing this decision; do not fill every row or compute a score.
A new local project alone does not require deep review, supply-chain auditing, or production gates.

## Fit check and execution boundary

- Propose one representative workflow and an observable success condition.
- Run a local, non-mutating check when authorized by the task; otherwise describe the next test.
- Installing or running an external candidate, creating a prototype, migrating data, or writing to
  external services requires task authorization. This research Skill does not supply it.
- Increase testing for actual integration risks, not hypothetical edge cases. A static method comparison
  does not need rollback machinery. Unverified fit is a reason to limit adoption, not to invent evidence.

## Output and project documents

Use the user's language. Usually a short recommendation covers:

- the current choice and preferred route;
- the few references that support it and what was actually checked;
- the important mismatch or non-transferable part;
- one next fit check.

Combine these naturally; no fixed headings, tables, or minimum source count are required.
Keep a quick pass in the conversation. An architectural consequence does not by itself authorize
writing documents or memory. Once approved, update the project's existing architecture or handoff
through its normal document workflow. Create a separate research note only when explicitly needed;
do not accumulate search logs or generate RELATED_WORK, an ADR, and a report for the same decision.

## Playbook integration

- `project-lifecycle`, when present, owns the mode, project stage, and next deliverable.
  Scout supplies evidence at an open choice; it does not restart that process.
- Bootstrap owns installation. Deciding a direction may benefit from Scout before bootstrap;
  merely installing Playbook into a decided project does not need another reference pass.
- Keep one user-level installation for pre-project discovery. Do not copy this body into project AGENTS.
- Personal coordination or memory integrations are optional and governed separately by the host.
  No Notion, projectmem, Supabase, or background service is required.

See [attribution](ATTRIBUTION.md) for the supplied draft's inspirations.
