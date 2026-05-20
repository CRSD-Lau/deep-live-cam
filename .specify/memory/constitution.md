# Neil Project Constitution

## Core Principles

### I. Specify Outcomes Before Code
Every substantial feature starts with a Spec Kit specification that states the user outcome, success criteria, constraints, and non-goals before implementation details. Plans must explain the chosen technical approach and identify affected files, data, tests, and user workflows.

### II. Respect The Existing System
Implementation follows the repository's current architecture, commands, naming, formatting, and dependency patterns. Prefer small, reversible changes over speculative rewrites, and preserve existing agent or project instructions in `AGENTS.md` and nearby documentation.

### III. Test Risky Behavior
Changes that affect user-facing behavior, parsing, persistence, auth, deployment, generated documents, or shared interfaces need focused validation. If a test is impractical, the plan or final notes must explain the manual verification performed and the residual risk.

### IV. Keep Quality Gates Visible
Plans and task lists must include the relevant build, lint, type-check, test, security, and documentation checks for the project. Do not mark work complete until the appropriate checks have run or a clear blocker is recorded.

### V. Deliverables Belong To Neil
Generated documents and packaged deliverables with editable metadata must set Author/Creator and Last Modified By/Modifier to `Neil Mitchell` before delivery. This applies to `.pptx`, `.xlsx`, `.docx`, PDFs where practical, and packaged copies; verify metadata when Office files or final deliverables are involved.

## Development Workflow

Use Spec Kit in this order for meaningful work: `$speckit-specify`, `$speckit-clarify` when requirements are ambiguous, `$speckit-plan`, `$speckit-tasks`, `$speckit-analyze` for consistency, then `$speckit-implement`. Keep specs, plans, tasks, and documentation aligned with the actual code.

## Governance

This constitution is the default project standard for Neil's local repositories. Repo-specific `AGENTS.md`, README, deployment docs, and domain rules may add stricter requirements. Amend this file when a project develops durable conventions that future specs should inherit.

**Version**: 1.0.0 | **Ratified**: 2026-05-20 | **Last Amended**: 2026-05-20
