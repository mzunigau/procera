# Product Specification v1

## Product name
Working name: **Business Operations Platform**

## Problem statement
Many companies manage operational work across spreadsheets, chats, shared drives, and disconnected task boards.
This causes common problems:
- people do not know exactly what they must do
- process knowledge lives in PDFs or in a few experienced employees
- projects are tracked, but execution is inconsistent
- documents are scattered
- evidence is hard to retrieve during audits
- managers cannot easily see task ownership, bottlenecks, or traceability

## Product vision
Create a modular platform where business processes define expected work, projects organize execution, tasks guide each person, and documents/evidence keep the organization audit-ready.

## Primary goals
1. Reduce ambiguity in day-to-day work.
2. Standardize execution through reusable process definitions.
3. Centralize project, task, document, and evidence management.
4. Improve accountability through clear ownership and due dates.
5. Preserve audit traceability without making the product ISO-only.

## Non-goals for v1
- full BPMN engine
- advanced no-code workflow builder
- real-time collaborative document editing
- ERP replacement
- custom reporting engine for each tenant
- highly specialized compliance modules

## User roles
### Platform Administrator
- manages company setup
- manages users, roles, permissions
- can view all system-level records

### Process Owner
- creates and maintains reusable business processes
- defines process steps, instructions, evidence requirements, and approvals

### Project Manager
- creates projects
- applies processes/templates to projects
- assigns work and monitors progress

### Task Assignee
- performs assigned work
- uploads evidence
- updates status
- adds comments

### Approver / Reviewer
- reviews task outputs, controlled documents, or evidence submissions
- approves or rejects when applicable

### Auditor / Read-only Reviewer
- reviews records, history, evidence, and document versions
- limited editing rights

## Core use cases
### 1. Create a reusable process
A process owner defines a standard company workflow with ordered steps, responsibilities, instructions, and required evidence.

### 2. Start a project
A manager creates a project and optionally applies one or more processes or templates.

### 3. Generate work from a process
The system creates task instances based on process steps and assigns them according to predefined roles or selected users.

### 4. Guide task execution
When a user opens a task, the task clearly shows:
- what to do
- what instructions/manuals apply
- what evidence must be attached
- whether approval is needed
- due date and status

### 5. Control documents
Controlled documents have versions, review/approval status, change summaries, and historical traceability.

### 6. Retrieve audit evidence
An auditor or manager can review project history, task changes, document revisions, approvals, timestamps, and uploaded evidence.

## Functional requirements
### Companies and access
- support multi-company separation from the start
- support users, roles, and permission-based access
- enforce tenant isolation

### Projects
- create, update, archive projects
- assign members to projects
- track project status, owner, dates, and progress
- allow process instances within projects

### Tasks
- create tasks manually or from a process step
- support subtasks later, but not required in the first slice
- support assignee, due date, status, priority, comments, attachments
- support board/list/calendar views
- keep history of key status changes

### Processes
- create reusable process definitions
- define ordered steps
- define responsible role or default assignee
- define instructions/manual references per step
- define whether evidence or approval is required
- define expected duration or SLA

### Documents
- distinguish controlled documents from casual attachments
- support document version history
- support statuses such as draft, in_review, approved, obsolete
- keep approver and approval timestamp

### Evidence
- allow evidence uploads or notes tied to tasks or process steps
- optionally require evidence before completion
- support approval/rejection of evidence when needed

### Audit
- log key sensitive actions
- support audit views by project, task, process, and document
- preserve historical state and actor/time details

## Success metrics
- reduced overdue tasks
- reduced time to onboard new staff into a process
- reduced time to retrieve evidence for audits
- percentage of process-based tasks vs unstructured tasks
- project completion visibility

## MVP definition
The first usable version should include:
- auth and tenants
- users and roles
- project CRUD
- task CRUD and board view
- process CRUD with ordered steps
- task generation from a process into a project
- comments and attachments
- basic audit log for key actions

## Future directions
- templates for common business projects
- process KPIs and bottleneck analytics
- document expiry alerts
- notifications and reminders
- configurable workflow transitions
- dashboard by role
