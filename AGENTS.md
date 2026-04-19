# AGENTS.md

## Purpose
This repository contains a modular web platform for business operations management.
The product combines:
- project management
- process execution
- task guidance by role
- document control
- audit traceability
- optional ISO support

The system is **not** limited to software teams.
It must work for operations, quality, HR, administration, procurement, and other business areas.

## Product vision
The platform should help an organization:
- define standard processes
- turn those processes into executable work
- tell each person what they must do
- keep documentation and evidence organized
- maintain traceability for audits

Core flow:
1. A company defines a process.
2. The process contains ordered steps, responsibilities, instructions, and required evidence.
3. A project is created from one or more processes or templates.
4. The system generates or guides tasks from those process steps.
5. Users complete work, upload evidence, and move tasks through status.
6. The platform keeps an audit trail of changes, approvals, and document history.

## Primary domain concepts
Use these concepts consistently in code, API names, and UI labels:

- **Company**: tenant or organization using the platform
- **User**: person using the platform
- **Role**: permission and operational responsibility
- **Process**: reusable business workflow definition
- **Process Step**: ordered instruction within a process
- **Manual / Instruction**: operational guidance attached to a process or step
- **Project**: execution container for a business initiative or operational case
- **Task**: unit of work assigned to a person or role
- **Document**: controlled file or record
- **Evidence**: file, note, form, or approval proving work was completed
- **Audit Log**: immutable traceability record
- **Template**: reusable preset for projects, processes, tasks, or documents

## Scope boundaries
This product is closer to:
- a business project platform
- a process execution system
- a document and evidence control system

It is **not** primarily:
- a developer-only sprint tool
- a pure BPM suite clone
- a generic file drive
- an ISO-only checklist app

ISO support is an important capability, but the core product must remain broadly useful for any company.

## UX principles
- Prefer simple business language over agile jargon.
- Use labels like `Project`, `Task`, `Process`, `Step`, `Document`, `Approval`, `Evidence`.
- Avoid forcing terms like `Epic`, `Sprint`, `Story`, or `Backlog` unless explicitly added as optional features.
- Each task view must clearly answer:
  - what should I do?
  - why does it matter?
  - what evidence is required?
  - what document or instruction should I read?
  - who approves this?
- The UI should reduce ambiguity for non-technical users.

## Functional priorities
Build in this order unless the user explicitly requests otherwise:

### Phase 1: platform foundation
- authentication
- companies / tenants
- users and roles
- base layout and navigation
- permissions model

### Phase 2: projects and tasks
- create projects
- create task boards
- create tasks and subtasks
- assign owners
- statuses, priorities, due dates
- comments and attachments
- list / board / calendar views

### Phase 3: processes
- create reusable processes
- define ordered process steps
- define responsible role or person per step
- attach instructions, forms, or manuals to steps
- allow projects to instantiate work from a process

### Phase 4: documents and evidence
- upload and classify documents
- relate documents to projects, tasks, processes, or steps
- version controlled documents
- evidence uploads for task completion
- approval workflow for controlled documents

### Phase 5: traceability and audit
- full audit log
- status transition history
- approvals and timestamps
- who changed what and when
- document revision history

### Phase 6: reporting and templates
- dashboards
- overdue work
- workload by user or role
- project progress
- process performance
- reusable templates for projects and processes

## Architectural principles
- Use a modular architecture.
- Keep business rules outside the UI layer.
- Prefer explicit domain services over bloated controllers.
- Separate reusable process definitions from project execution instances.
- Design for auditability from the start.
- Every important state transition should be traceable.
- Prefer composition over deeply coupled modules.

## Suggested domain separation
Use this as the default feature structure unless a better justified structure is proposed:

- `auth/`
- `companies/`
- `users/`
- `roles/`
- `projects/`
- `tasks/`
- `processes/`
- `documents/`
- `approvals/`
- `audit/`
- `templates/`
- `reports/`
- `shared/`

## Recommended entity model
Use these as anchor entities:
- Company
- User
- Role
- Project
- ProjectMember
- Task
- TaskComment
- TaskAttachment
- Process
- ProcessStep
- ProcessStepInstruction
- ProjectProcessInstance
- Document
- DocumentVersion
- Evidence
- Approval
- AuditLog
- Template

## Data modeling rules
- Always include `id`, `created_at`, `updated_at`.
- Use soft delete only when business value clearly exists.
- Keep immutable history for audit-relevant records.
- Distinguish clearly between:
  - process definition
  - project instance
  - task execution
- Do not mix current document metadata with historical versions.
- Use enums carefully; if statuses may vary by tenant or workflow, prefer configurable status models.

## Task and process behavior rules
- A task may be created manually or generated from a process step.
- If a task is generated from a process step, keep a persistent reference to that source step.
- A process step can define:
  - responsible role
  - description of work
  - required evidence
  - expected duration or SLA
  - approval requirement
  - linked manuals or forms
- Completing a task should optionally require evidence or approval depending on process rules.

## Document control rules
- Treat controlled documents separately from casual attachments.
- Controlled documents should support:
  - version number
  - status (`draft`, `in_review`, `approved`, `obsolete`)
  - approver
  - approval timestamp
  - change summary
- Never overwrite historical document versions.
- Evidence files may be immutable after final submission unless reopened by authorized users.

## Auditability rules
Every important business action should be logged, especially:
- project creation
- task assignment
- task status change
- approval / rejection
- process publication
- document version creation
- document approval
- evidence submission
- permission-sensitive changes

Audit records should capture:
- actor
- action
- target type
- target id
- timestamp
- relevant before/after summary when appropriate

## API and coding conventions
- Prefer descriptive names over abbreviations.
- Keep endpoints resource-oriented.
- Validate all inputs at the boundary.
- Return predictable error shapes.
- Write small reusable services for domain logic.
- Avoid hidden side effects.
- Add tests for critical domain rules.

## Frontend conventions
- Build reusable components for:
  - data tables
  - status badges
  - assignee selector
  - comments timeline
  - file upload
  - audit timeline
  - board columns
  - process step editor
- Prioritize clarity over visual complexity.
- The product should feel professional and operational, not playful.

## Security and permissions
- Enforce server-side authorization on every sensitive action.
- Never rely solely on frontend checks.
- Tenants must be isolated.
- Approval, audit, and document actions require stricter permission checks than basic viewing.
- Avoid exposing sensitive internal metadata unnecessarily.

## Testing expectations
At minimum, test:
- permissions
- process-to-task generation
- task status transitions
- approval flows
- document versioning
- audit log creation

## Definition of done
A feature is done only when:
- business behavior works end-to-end
- permissions are enforced
- edge cases are handled
- logs or traceability are considered where relevant
- code is understandable and reasonably modular
- tests cover the critical path
- documentation is updated if the feature changes workflow or conventions

## Do not do these by default
- Do not introduce unnecessary microservices.
- Do not use developer jargon in business-facing UI.
- Do not hardcode one company’s workflow as the universal model.
- Do not make ISO-specific assumptions the entire platform depends on.
- Do not create complex workflow builders too early.
- Do not optimize prematurely for enterprise-scale complexity before the core domain works.

## Preferred implementation mindset
When asked to build a feature, first identify:
1. which domain module owns it
2. whether it belongs to process definition or project execution
3. whether it affects auditability
4. whether it needs controlled documents or simple attachments
5. what permissions apply

Then implement the smallest clean version that preserves future extensibility.

## First milestone target
Unless the user asks otherwise, prioritize delivering this first usable slice:
- authentication
- company and user setup
- project CRUD
- task CRUD with board view
- process CRUD with ordered steps
- generate tasks from a process into a project
- comments and attachments
- basic audit log for key actions

## Repository notes
If the repository is still empty, scaffold it around the domain modules above.
If a framework is chosen later, adapt structure to that framework without breaking the domain boundaries in this file.

## Working style
- Explain tradeoffs when proposing architecture.
- Prefer incremental delivery.
- Keep commits focused.
- If something is ambiguous, choose the most general business-friendly design.
- Preserve a path toward multi-company support, configurable workflows, and audit-ready traceability.
