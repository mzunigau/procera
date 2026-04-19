# Data Model v1

This file defines the initial conceptual schema for the platform.
It is not the final SQL implementation, but it should guide the first database design and migrations.

## Shared conventions
All primary entities should include at minimum:
- id
- company_id when tenant-scoped
- created_at
- updated_at

Add `created_by` and `updated_by` where helpful for traceability.

## 1. Company
Represents a tenant organization.

Fields:
- id
- name
- slug
- status
- created_at
- updated_at

## 2. User
Represents a system user.

Fields:
- id
- company_id
- first_name
- last_name
- email
- password_hash
- status
- created_at
- updated_at

Relations:
- belongs to one company
- can have many roles
- can be assigned to many projects and tasks

## 3. Role
Represents both access control and operational responsibility labels.

Fields:
- id
- company_id
- name
- description
- created_at
- updated_at

Examples:
- Administrator
- Process Owner
- Project Manager
- Reviewer
- Auditor

## 4. UserRole
Join table for users and roles.

Fields:
- id
- company_id
- user_id
- role_id
- created_at

## 5. Project
Represents a business initiative or execution container.

Fields:
- id
- company_id
- name
- code (optional)
- description
- objective
- status
- start_date
- due_date
- owner_user_id
- created_at
- updated_at

Suggested statuses:
- draft
- active
- on_hold
- completed
- cancelled
- archived

## 6. ProjectMember
Represents project participation.

Fields:
- id
- company_id
- project_id
- user_id
- member_type
- created_at

Examples of member_type:
- owner
- contributor
- reviewer
- observer

## 7. Task
Represents a unit of work.

Fields:
- id
- company_id
- project_id
- process_step_id (nullable)
- parent_task_id (nullable)
- title
- description
- status
- priority
- assignee_user_id (nullable)
- assignee_role_id (nullable)
- due_date
- started_at (nullable)
- completed_at (nullable)
- requires_evidence (boolean)
- requires_approval (boolean)
- created_at
- updated_at

Suggested statuses:
- pending
- in_progress
- in_review
- blocked
- completed
- cancelled

Suggested priorities:
- low
- medium
- high
- critical

Rule:
If `process_step_id` is present, the task was generated from a process definition or is directly tied to a process step.

## 8. TaskComment
Task discussion timeline.

Fields:
- id
- company_id
- task_id
- author_user_id
- body
- created_at
- updated_at

## 9. TaskAttachment
Casual execution attachment tied to a task.

Fields:
- id
- company_id
- task_id
- file_name
- storage_key
- content_type
- size_bytes
- uploaded_by_user_id
- created_at

Important:
This is not the same as a controlled document.

## 10. Process
Reusable business workflow definition.

Fields:
- id
- company_id
- name
- code (optional)
- objective
- scope
- owner_user_id
- version_label (nullable)
- status
- created_at
- updated_at

Suggested statuses:
- draft
- published
- archived

## 11. ProcessStep
Ordered step inside a process.

Fields:
- id
- company_id
- process_id
- step_order
- name
- description
- responsible_role_id (nullable)
- responsible_user_id (nullable)
- instruction_summary (nullable)
- expected_duration_hours (nullable)
- sla_hours (nullable)
- requires_evidence (boolean)
- requires_approval (boolean)
- created_at
- updated_at

Important:
A process step defines what a person must do and what proof is expected.

## 12. ProcessStepInstruction
Detailed guidance/manual section linked to a process step.

Fields:
- id
- company_id
- process_step_id
- title
- content_markdown
- created_at
- updated_at

This allows the task to show operational instructions directly instead of only linking a PDF.

## 13. ProjectProcessInstance
Represents the use of a process inside a specific project.

Fields:
- id
- company_id
- project_id
- process_id
- name
- status
- started_at
- completed_at (nullable)
- created_at
- updated_at

Suggested statuses:
- pending
- active
- completed
- cancelled

This keeps reusable process definitions separate from active executions.

## 14. ProjectProcessStepInstance (optional but recommended)
Represents runtime state of each process step in a project.

Fields:
- id
- company_id
- project_process_instance_id
- process_step_id
- status
- assigned_user_id (nullable)
- assigned_role_id (nullable)
- due_date (nullable)
- started_at (nullable)
- completed_at (nullable)
- created_at
- updated_at

Suggested statuses:
- pending
- ready
- in_progress
- in_review
- completed
- skipped
- blocked

This entity becomes valuable if process tracking grows beyond simple task generation.

## 15. Document
Represents a controlled document record.

Fields:
- id
- company_id
- title
- document_type
- category
- current_version_id (nullable)
- owner_user_id
- status
- created_at
- updated_at

Suggested statuses:
- draft
- in_review
- approved
- obsolete

Examples of document_type:
- policy
- procedure
- manual
- template
- record
- form

## 16. DocumentVersion
Immutable version entry for a controlled document.

Fields:
- id
- company_id
- document_id
- version_number
- file_name
- storage_key
- content_type
- size_bytes
- change_summary
- status
- created_by_user_id
- approved_by_user_id (nullable)
- approved_at (nullable)
- created_at

Suggested statuses:
- draft
- in_review
- approved
- rejected
- obsolete

Rule:
Never overwrite historical versions.

## 17. DocumentLink
Associates a controlled document to business records.

Fields:
- id
- company_id
- document_id
- linked_type
- linked_id
- relation_type
- created_at

Examples:
- link a manual to a process step
- link a procedure to a process
- link a template to a project

## 18. Evidence
Represents proof tied to a task or process execution.

Fields:
- id
- company_id
- task_id (nullable)
- project_process_step_instance_id (nullable)
- evidence_type
- title
- notes (nullable)
- file_name (nullable)
- storage_key (nullable)
- submitted_by_user_id
- submitted_at
- status
- approved_by_user_id (nullable)
- approved_at (nullable)
- created_at
- updated_at

Suggested evidence_type:
- file
- note
- form
- link
- approval

Suggested statuses:
- submitted
- approved
- rejected

## 19. Approval
Generic approval record.

Fields:
- id
- company_id
- approval_type
- target_type
- target_id
- requested_by_user_id
- assigned_to_user_id
- decision
- comment (nullable)
- requested_at
- decided_at (nullable)
- created_at
- updated_at

Suggested decisions:
- pending
- approved
- rejected
- cancelled

Examples:
- approve document version
- approve task completion
- approve evidence submission

## 20. AuditLog
Immutable business traceability record.

Fields:
- id
- company_id
- actor_user_id
- action
- target_type
- target_id
- summary
- before_data_json (nullable)
- after_data_json (nullable)
- created_at

Important:
Keep the record append-only.

## 21. Template
Reusable setup artifact.

Fields:
- id
- company_id
- template_type
- name
- description
- payload_json
- created_at
- updated_at

Examples of template_type:
- project
- process
- task_set

## Key relationships summary
- Company 1---N Users
- Company 1---N Roles
- User N---N Roles through UserRole
- Company 1---N Projects
- Project 1---N Tasks
- Process 1---N ProcessSteps
- Project 1---N ProjectProcessInstances
- ProjectProcessInstance N---1 Process
- Task N---1 ProcessStep (optional)
- Document 1---N DocumentVersions
- Document N---N business records through DocumentLink
- Task 1---N Evidence
- Task 1---N TaskComments
- Task 1---N TaskAttachments

## Recommended first migration order
1. companies
2. users, roles, user_roles
3. projects, project_members
4. processes, process_steps, process_step_instructions
5. tasks, task_comments, task_attachments
6. project_process_instances
7. documents, document_versions, document_links
8. evidence, approvals
9. audit_logs
10. templates

## Notes for v1 implementation
- start with simple enums in code for statuses
- if tenant-specific statuses are needed later, introduce configurable workflow tables
- task generation may start by creating tasks directly from process steps
- introduce `project_process_step_instance` only if runtime process visibility becomes necessary in the first milestone
