# Business Operations Platform

A modular web platform for companies to manage projects, tasks, processes, documents, and audit traceability.

## Product summary
This product is designed for companies that need more than a simple task board.
It combines:
- project management
- task execution
- process-based work guidance
- document and evidence control
- audit traceability
- optional support for ISO-style compliance needs

The main idea is simple:
**processes define how work should be done, projects execute that work, tasks guide each person, and documents/evidence prove what happened.**

## Target users
This platform is intended for non-technical and mixed teams, including:
- operations
- quality
- administration
- HR
- procurement
- customer service
- project teams

It should not depend on software-only language such as sprint, story, epic, or backlog.
Those concepts can be added later as optional views, but the core vocabulary should remain business-friendly.

## Core product pillars
1. **Projects**: business initiatives or execution containers.
2. **Tasks**: units of work assigned to users or roles.
3. **Processes**: reusable workflows that define what each person should do.
4. **Documents**: controlled files, instructions, manuals, or records.
5. **Evidence**: proof that work was completed.
6. **Audit**: traceability of key actions and approvals.

## Core flow
1. A company creates a process.
2. The process contains ordered steps, roles, instructions, expected evidence, and approval requirements.
3. A project is created manually or from a template.
4. The project uses one or more processes.
5. The system creates or guides tasks from the process steps.
6. Users perform tasks, upload evidence, and move work through statuses.
7. The platform stores audit history and document revisions.

## Repository structure
```text
/backend
  /modules
    /auth
    /companies
    /users
    /roles
    /projects
    /tasks
    /processes
    /documents
    /approvals
    /audit
    /templates
    /reports
    /shared

/frontend
  /components
  /pages
  /features

/docs
  architecture.md
  roadmap.md
  product-spec.md

/database
  schema.md
```

## Recommended initial stack
### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy or SQLModel
- PostgreSQL
- Alembic for migrations
- Pytest

### Frontend
- React
- TypeScript
- Vite
- TanStack Query
- React Router
- Tailwind CSS

### Optional later additions
- object storage for documents (S3-compatible)
- background jobs for notifications
- search indexing for documents and audit records

## Recommended development milestones
### Milestone 1
- authentication
- companies / tenants
- users and roles
- project CRUD
- task CRUD
- board view
- comments and attachments

### Milestone 2
- process CRUD
- ordered process steps
- instructions/manuals linked to steps
- generate tasks from process steps into a project

### Milestone 3
- documents
- version control
- evidence submission
- approvals
- basic audit trail

### Milestone 4
- dashboards
- templates
- overdue alerts
- workload and process performance reports

## Local development placeholders
These commands are placeholders and should be updated once the stack is scaffolded.

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
pytest
npm test
```

## Definition of done
A feature is complete only when:
- business behavior works end-to-end
- authorization is enforced server-side
- important state changes are traceable when relevant
- validation and common edge cases are handled
- tests cover the critical path
- documentation is updated when behavior changes

## Important design rules
- Keep process definitions separate from project execution.
- Do not mix controlled documents with casual file attachments.
- Do not build the product around one company's workflow.
- Prefer simple business language in the UI.
- Design with auditability in mind from the beginning.

See `AGENTS.md` for implementation guidance for Codex and `/docs` for product and architecture details.
