# {{PROJECT_NAME}} Architecture

Last updated: not started

## System shape

Describe the smallest verified system shape.

## Entry points

- User entry: not verified.
- Program entry: not verified.

## Command map

| Action | Working directory | Command | Status |
| --- | --- | --- | --- |
| Start | project root | Not verified yet | unverified |
| Test | project root | Not verified yet | unverified |
| Lint | project root | Not verified yet | unverified |
| Staging | project root | Not verified or not applicable | unverified |
| Build release | project root | Not verified or not applicable | unverified |
| Deploy | controlled production entry | Not verified or not applicable | unverified |
| Rollback | controlled production entry | Not verified or not applicable | unverified |

## Important components

- Not verified yet.

## Data flow

- Not verified yet.

## High-risk areas

- External side effects: not verified.
- Credentials and private data: not verified.

## Environment isolation

| Environment | Runtime data root | Ports/services | Credentials | External writes |
| --- | --- | --- | --- | --- |
| development | Not verified | Not verified | Not verified | disabled or not verified |
| test | Not verified | Not verified | test-only or not verified | disabled |
| staging | Not verified or not applicable | Not verified | staging-only or not applicable | controlled |
| production | Not verified or not applicable | Not verified | production-only or not applicable | explicitly authorized |

## Deployment and rollback

- Project classification: formal, standard, experiment, or documentation-only; not classified.
- Reviewed source branch: Not verified.
- Immutable release or fixed-version mechanism: Not verified or not applicable.
- Deployment action and required confirmation: Not verified or not applicable.
- Backup and active-task checks: Not verified or not applicable.
- Rollback target and command: Not verified or not applicable.
- Production-data migration path: separate authorization required or not applicable.

## Verification

- Minimum verification entry: not verified.
