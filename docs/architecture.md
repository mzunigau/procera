# Architecture Overview

## Architectural style
Use a modular monolith as the default starting architecture.

Why:
- faster to build and iterate
- easier for Codex to scaffold consistently
- better fit for a new product with evolving domain rules
- audit and process logic remain easier to reason about than in premature microservices

## Logical layers
### 1. Presentation layer
- REST API backend
- web frontend
- optional admin pages and audit views

### 2. Application layer
- use cases / services
- transaction boundaries
- orchestration between modules

### 3. Domain layer
- entities
- domain services
- business rules
- status transition rules
- audit triggers

### 4. Infrastructure layer
- database
- document storage
- background jobs (later)
- email/notification adapters (later)

## High-level modules
### auth
Authentication and session/token management.

### companies
Tenant model and organization-level settings.

### users
User profiles and assignments.

### roles
Permissions and operational responsibility definitions.

### projects
Project lifecycle, members, and progress.

### tasks
Task execution, comments, attachments, statuses, assignees.

### processes
Reusable process definitions and ordered steps.

### documents
Controlled documents, versions, classification, approvals.

### approvals
Approval rules and approval records.

### audit
Immutable traceability records.

### templates
Reusable project/process starting structures.

### reports
Read-model oriented metrics and dashboards.

## Core design distinction
Keep these concepts separate:

### Process definition
Reusable standard workflow. Does not represent one active business case.

### Project execution
A real initiative or operational case that may instantiate one or more processes.

### Task execution
A concrete piece of work assigned to a user or role, either manually created or generated from a process step.

### Controlled document
A governed document with versioning, review, approval, and historical retention.

### Attachment / evidence
A file or record used during execution and linked to a task or project.

## Suggested backend package structure
```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      database.py
    modules/
      auth/
      companies/
      users/
      roles/
      projects/
      tasks/
      processes/
      documents/
      approvals/
      audit/
      templates/
      reports/
    shared/
      enums/
      exceptions/
      utils/
      schemas/
      mixins/
```

## Module internal structure pattern
Use the same pattern inside each domain module where possible:
```text
module/
  api.py
  service.py
  repository.py
  models.py
  schemas.py
  rules.py
```

This keeps generation predictable for Codex.

## Event and audit strategy
Every critical state transition should create an audit record.

Recommended events to log:
- project created
- project updated
- project archived
- task created
- task assigned
- task status changed
- process created
- process published
- process step updated
- document version created
- document approved/rejected
- evidence submitted
- approval granted/rejected
- permission-sensitive changes

Audit records should contain:
- actor_id
- company_id
- action
- target_type
- target_id
- timestamp
- summary
- before_data (optional/sanitized)
- after_data (optional/sanitized)

## Document storage strategy
For v1:
- metadata in PostgreSQL
- file binaries in local storage for development
- abstract storage behind a service so S3-compatible storage can be added later

## Authorization model
Use role-based access control plus scoped permissions.

Examples:
- project managers can manage projects they own or belong to
- process owners can publish processes
- approvers can approve only allowed artifacts
- auditors can view but not modify most records

Always enforce permissions server-side.

## Frontend page map
### Auth
- login
- forgot password later

### Main navigation
- dashboard
- projects
- tasks
- processes
- documents
- reports
- settings

### Project views
- project list
- project detail
- project board
- project calendar
- project members
- project documents
- project audit timeline

### Process views
- process list
- process detail
- process step editor
- linked documents/manuals

### Task views
- my tasks
- board
- task detail with instructions and evidence section

### Document views
- document list
- document detail
- version history
- approval state

## API design guidelines
- use resource-oriented endpoints
- avoid generic `/action` endpoints when a nested resource is clearer
- return stable response shapes
- validate input at the API boundary
- keep business logic out of route handlers

Examples:
- `POST /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/tasks`
- `POST /processes/{process_id}/steps`
- `POST /projects/{project_id}/process-instances`
- `POST /project-process-instances/{id}/generate-tasks`
- `POST /tasks/{task_id}/evidence`
- `POST /documents/{document_id}/versions`

## Initial technical decisions
- start with synchronous request-response flows
- use background jobs only when a real need appears
- avoid CQRS/event sourcing complexity for v1
- maintain audit history through explicit logging and immutable version tables

## Testing priorities
1. tenant isolation
2. permissions
3. process-to-task generation
4. task status transitions
5. document versioning
6. approval flows
7. audit log creation
