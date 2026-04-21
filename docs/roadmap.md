# Implementation Roadmap

## Principle
Build the smallest useful operational slice first.
Do not start with advanced compliance features before the project/task/process loop is working.

## Phase 0 - project bootstrap
Deliverables:
- repository scaffold
- AGENTS.md
- README.md
- architecture.md
- schema.md
- initial stack choice
- lint/test tooling

Exit criteria:
- repository structure exists
- development commands are documented
- Codex has enough context to scaffold consistently

## Phase 1 - foundation
Deliverables:
- auth
- company model
- users and roles
- permission middleware / guards
- base frontend shell

Exit criteria:
- users can log in
- tenant isolation exists
- permissions can protect endpoints

## Phase 2 - projects and tasks
Deliverables:
- project CRUD
- project members
- task CRUD
- comments
- attachments
- board/list views

Exit criteria:
- a manager can create a project
- users can create and update tasks
- assignees can see what they own

## Phase 3 - processes
Deliverables:
- process CRUD
- ordered steps
- step instructions
- role/user responsibility per step
- create project from process or apply process to project
- generate tasks from process

Exit criteria:
- a reusable process can be created
- a project can instantiate work from that process
- generated tasks preserve references to source steps

## Phase 4 - documents and evidence
Deliverables:
- controlled document CRUD
- document versions
- document links to processes/steps/projects
- evidence submissions on tasks
- simple approval flow

Exit criteria:
- tasks can require evidence
- process steps can point to instructions/manuals
- document history is retained

## Phase 5 - audit and reporting
Deliverables:
- audit timeline
- status history
- key dashboards
- overdue work report
- basic workload report

Exit criteria:
- an auditor or manager can review who changed what and when
- managers can identify bottlenecks and overdue items

## Suggested first API slice
- `POST /auth/login`
- `GET /me`
- `POST /projects`
- `GET /projects`
- `GET /projects/{id}`
- `POST /projects/{id}/tasks`
- `PATCH /tasks/{id}`
- `POST /processes`
- `POST /processes/{id}/steps`
- `POST /projects/{id}/process-instances`
- `POST /project-process-instances/{id}/generate-tasks`
- `POST /tasks/{id}/comments`
- `POST /tasks/{id}/attachments`

## Suggested first frontend pages
- login
- dashboard shell
- projects list
- project detail
- task board
- task detail drawer/page
- processes list
- process editor

## Testing roadmap
### Phase 1 tests
- login
- permission enforcement
- tenant isolation

### Phase 2 tests
- project CRUD
- task CRUD
- task assignment visibility

### Phase 3 tests
- process creation
- process step order validation
- process-to-task generation

### Phase 4 tests
- document version immutability
- evidence requirement enforcement
- approval decisions

### Phase 5 tests
- audit event creation
- audit filters
- report query correctness

## Product decisions to postpone
- custom workflow designer
- process branching/conditions
- advanced notification engine
- recurring tasks
- complex Gantt engine
- public API integrations

## Stabilization checklist before adding more modules

Use this checklist to decide what to harden before expanding the domain surface.

Status legend:
- `[x]` implemented enough for the current prototype
- `[~]` partially implemented, needs hardening
- `[ ]` not implemented yet

### Current completed baseline
- [x] Modular FastAPI backend structure for projects, tasks, processes, process steps, documents, audit, templates, users, and roles.
- [x] React frontend shell with dashboard, projects, tasks, processes, documents, and templates views.
- [x] Project CRUD and task CRUD with board/list views.
- [x] Task comments and task attachments.
- [x] Process CRUD with ordered process steps.
- [x] Project creation from a process generates tasks from process steps.
- [x] Controlled documents with upload, links, and version history.
- [x] Basic templates from process/project and project creation from template.
- [x] Users, roles, user-role assignments, and derived permission lookup.
- [x] Backend tests for critical current flows.

### Priority 0 - start here
- [x] Add backend user/tenant context instead of trusting `company_id` from request bodies.
  - Why: tenant isolation is the foundation for every module.
  - Current status: implemented with `RequestContext`, `X-Procera-User-Id`, and temporary development header `X-Procera-Company-Id`.
  - Next hardening: replace development headers with real authentication/session context.
- [x] Enforce permission guards on sensitive endpoints.
  - Why: users/roles exist, but permissions do not protect project, task, process, document, template, audit, or user actions yet.
  - Current status: implemented with `require_permission()` on sensitive project, task, process, document, template, audit, user, and role endpoints.
  - Next hardening: remove the temporary development-context bypass when authentication is implemented.
- [x] Add service-level transaction boundaries for multi-step operations.
  - Why: process-to-project generation and templates create multiple records; partial failures can leave inconsistent data.
  - Current status: project creation from process and project creation from template now commit atomically and roll back partial records on failures.
- [x] Validate user and role references across existing modules.
  - Why: `owner_user_id`, `assignee_user_id`, `assignee_role_id`, `responsible_user_id`, and `responsible_role_id` can point to missing or cross-company records.
  - Current status: services validate user and role references against the current company for projects, processes, process steps, tasks, documents, and template instantiation.

### Priority 1 - do next
- [x] Add `ProjectProcessInstance` minimum.
  - Why: current task generation preserves `process_step_id`, but does not explicitly record that a project instantiated a process.
  - Current status: projects can record process instances, generate tasks from an instance, and project creation with `process_id` records an active instance.
- [ ] Complete audit coverage for core modules.
  - Why: tasks log key events, but projects, processes, documents, templates, users, and roles are incomplete.
  - Current status: tasks, templates, project create/update, process instance creation, and process-instance task generation write audit logs.
  - Start with: project created/updated, process published, document version created, template instantiated, role assigned.
- [ ] Add structured template payload validation.
  - Why: `payload_json` is flexible and can fail at runtime when required keys are missing.
  - Start with: Pydantic payload schemas for process templates and project templates.
- [ ] Introduce database migrations.
  - Why: startup `create_all` is acceptable for prototype work but not for controlled schema evolution.
  - Start with: Alembic baseline migration from the current model.

### Priority 2 - improve after the foundation is safer
- [ ] Replace manual frontend IDs with real selectors.
  - Why: company, user, role, author, uploader, and assignee fields are currently typed manually in several views.
  - Start with: assignee selector and owner selector using users/roles.
- [ ] Extract shared frontend components.
  - Why: forms and timelines are growing inside feature views.
  - Start with: `AssigneeSelector`, `CompanyContext`, `ActivityTimeline`, `FileUpload`, `ProjectForm`, and `TemplateForm`.
- [ ] Document current status contracts.
  - Why: current task state uses `review`, while the conceptual schema suggests `in_review`.
  - Start with: a small status reference section in architecture or schema notes.
- [ ] Add pagination and filtering to list endpoints.
  - Why: current endpoints return full lists and dashboard/views load several lists at once.
  - Start with: tasks, audit logs, documents, and templates.

### Recommended next implementation
Start with **Priority 1: audit coverage for core modules**.

The current product now has tenant context, permission guards, transaction boundaries, reference validation, and process instantiation tracking. Extending audit coverage next will make the operational workflows easier to trust before adding companies, approvals, evidence, reports, or more workflow features.
