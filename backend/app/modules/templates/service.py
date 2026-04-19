from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.audit.repository import AuditLogRepository
from app.modules.audit.schemas import AuditLogCreate
from app.modules.process_steps.repository import ProcessStepRepository
from app.modules.process_steps.schemas import ProcessStepCreate
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schemas import ProcessCreate
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import ProjectCreate
from app.modules.tasks.models import TaskPriority, TaskStatus
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate
from app.modules.templates.models import Template, TemplateType
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schemas import (
    ProjectFromTemplateCreate,
    TemplateCreate,
    TemplateFromSourceCreate,
    TemplateUpdate,
)


class TemplateService:
    def __init__(self, db: Session) -> None:
        self.templates = TemplateRepository(db)
        self.projects = ProjectRepository(db)
        self.processes = ProcessRepository(db)
        self.process_steps = ProcessStepRepository(db)
        self.tasks = TaskRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_templates(
        self,
        company_id: str | None = None,
        template_type: TemplateType | None = None,
    ) -> list[Template]:
        return self.templates.list(company_id=company_id, template_type=template_type)

    def get_template(self, template_id: str) -> Template:
        template = self.templates.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Template not found"},
            )
        return template

    def create_template(self, data: TemplateCreate) -> Template:
        template = self.templates.create(data)
        self._record_template_audit("template.created", template, "Template created")
        return template

    def update_template(self, template_id: str, data: TemplateUpdate) -> Template:
        template = self.get_template(template_id)
        updated = self.templates.update(template, data)
        self._record_template_audit("template.updated", updated, "Template updated")
        return updated

    def delete_template(self, template_id: str) -> None:
        template = self.get_template(template_id)
        self.templates.delete(template)

    def create_from_process(self, process_id: str, data: TemplateFromSourceCreate) -> Template:
        process = self.processes.get(process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process does not exist"},
            )
        if process.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process belongs to a different company"},
            )

        steps = self.process_steps.list(company_id=data.company_id, process_id=process_id)
        template = self.templates.create(
            TemplateCreate(
                company_id=data.company_id,
                template_type=TemplateType.PROCESS,
                name=data.name,
                description=data.description,
                payload_json={
                    "process": {
                        "name": process.name,
                        "code": process.code,
                        "objective": process.objective,
                        "scope": process.scope,
                        "owner_user_id": process.owner_user_id,
                        "version_label": process.version_label,
                        "status": process.status.value,
                    },
                    "steps": [self._process_step_payload(step) for step in steps],
                },
            )
        )
        self._record_template_audit(
            "template.created_from_process",
            template,
            f"Template created from process {process.name}",
        )
        return template

    def create_from_project(self, project_id: str, data: TemplateFromSourceCreate) -> Template:
        project = self.projects.get(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Project does not exist"},
            )
        if project.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Project belongs to a different company"},
            )

        tasks = self.tasks.list(company_id=data.company_id, project_id=project_id)
        template = self.templates.create(
            TemplateCreate(
                company_id=data.company_id,
                template_type=TemplateType.PROJECT,
                name=data.name,
                description=data.description,
                payload_json={
                    "project": {
                        "code": project.code,
                        "description": project.description,
                        "objective": project.objective,
                        "status": project.status.value,
                        "owner_user_id": project.owner_user_id,
                    },
                    "tasks": [self._task_structure_payload(task) for task in tasks],
                },
            )
        )
        self._record_template_audit(
            "template.created_from_project",
            template,
            f"Template created from project {project.name}",
        )
        return template

    def create_project_from_template(
        self,
        template_id: str,
        data: ProjectFromTemplateCreate,
    ) -> Project:
        template = self.get_template(template_id)
        if template.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Template belongs to a different company"},
            )

        if template.template_type == TemplateType.PROCESS:
            return self._create_project_from_process_template(template, data)
        if template.template_type == TemplateType.PROJECT:
            return self._create_project_from_project_template(template, data)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Template type cannot create a project"},
        )

    def _create_project_from_process_template(
        self,
        template: Template,
        data: ProjectFromTemplateCreate,
    ) -> Project:
        process_payload = template.payload_json.get("process")
        if not isinstance(process_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Template payload does not include a process"},
            )

        process = self.processes.create(
            ProcessCreate(
                company_id=data.company_id,
                name=str(process_payload.get("name") or template.name),
                code=process_payload.get("code"),
                objective=process_payload.get("objective"),
                scope=process_payload.get("scope"),
                owner_user_id=process_payload.get("owner_user_id"),
                version_label=process_payload.get("version_label"),
                status=process_payload.get("status", "draft"),
            )
        )

        for step_payload in self._payload_list(template.payload_json.get("steps")):
            self.process_steps.create(
                ProcessStepCreate(
                    company_id=data.company_id,
                    process_id=process.id,
                    step_order=step_payload["step_order"],
                    name=step_payload["name"],
                    description=step_payload.get("description"),
                    responsible_role_id=step_payload.get("responsible_role_id"),
                    responsible_user_id=step_payload.get("responsible_user_id"),
                    instruction_summary=step_payload.get("instruction_summary"),
                    expected_duration_hours=step_payload.get("expected_duration_hours"),
                    sla_hours=step_payload.get("sla_hours"),
                    requires_evidence=step_payload.get("requires_evidence", False),
                    requires_approval=step_payload.get("requires_approval", False),
                )
            )

        project = self._create_project(data, process_id=process.id)
        self._generate_tasks_from_process(project, process.id)
        self._record_project_audit(
            "project.created_from_template",
            project,
            f"Project created from template {template.name}",
            {"template_id": template.id, "template_type": template.template_type.value},
        )
        return project

    def _create_project_from_project_template(
        self,
        template: Template,
        data: ProjectFromTemplateCreate,
    ) -> Project:
        project = self._create_project(data)
        for task_payload in self._payload_list(template.payload_json.get("tasks")):
            self.tasks.create(
                TaskCreate(
                    company_id=data.company_id,
                    project_id=project.id,
                    process_step_id=task_payload.get("process_step_id"),
                    title=task_payload["title"],
                    description=task_payload.get("description"),
                    status=TaskStatus.PENDING,
                    priority=task_payload.get("priority", TaskPriority.MEDIUM),
                    assignee_user_id=task_payload.get("assignee_user_id"),
                    assignee_role_id=task_payload.get("assignee_role_id"),
                    requires_evidence=task_payload.get("requires_evidence", False),
                    requires_approval=task_payload.get("requires_approval", False),
                )
            )

        self._record_project_audit(
            "project.created_from_template",
            project,
            f"Project created from template {template.name}",
            {"template_id": template.id, "template_type": template.template_type.value},
        )
        return project

    def _create_project(
        self,
        data: ProjectFromTemplateCreate,
        process_id: str | None = None,
    ) -> Project:
        return self.projects.create(
            ProjectCreate(
                company_id=data.company_id,
                name=data.name,
                code=data.code,
                description=data.description,
                objective=data.objective,
                status=data.status,
                start_date=data.start_date,
                due_date=data.due_date,
                owner_user_id=data.owner_user_id,
                process_id=process_id,
            )
        )

    def _generate_tasks_from_process(self, project: Project, process_id: str) -> None:
        process_steps = self.process_steps.list(
            company_id=project.company_id,
            process_id=process_id,
        )
        for process_step in process_steps:
            self.tasks.create(
                TaskCreate(
                    company_id=project.company_id,
                    project_id=project.id,
                    process_step_id=process_step.id,
                    title=process_step.name,
                    description=process_step.description,
                    assignee_user_id=process_step.responsible_user_id,
                    assignee_role_id=process_step.responsible_role_id,
                    requires_evidence=process_step.requires_evidence,
                    requires_approval=process_step.requires_approval,
                )
            )

    def _payload_list(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _process_step_payload(self, step: Any) -> dict[str, Any]:
        return {
            "step_order": step.step_order,
            "name": step.name,
            "description": step.description,
            "responsible_role_id": step.responsible_role_id,
            "responsible_user_id": step.responsible_user_id,
            "instruction_summary": step.instruction_summary,
            "expected_duration_hours": step.expected_duration_hours,
            "sla_hours": step.sla_hours,
            "requires_evidence": step.requires_evidence,
            "requires_approval": step.requires_approval,
        }

    def _task_structure_payload(self, task: Any) -> dict[str, Any]:
        return {
            "process_step_id": task.process_step_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "assignee_user_id": task.assignee_user_id,
            "assignee_role_id": task.assignee_role_id,
            "requires_evidence": task.requires_evidence,
            "requires_approval": task.requires_approval,
        }

    def _record_template_audit(self, action: str, template: Template, summary: str) -> None:
        self.audit_logs.create(
            AuditLogCreate(
                company_id=template.company_id,
                action=action,
                target_type="template",
                target_id=template.id,
                summary=summary,
                after_data_json={
                    "name": template.name,
                    "template_type": template.template_type.value,
                },
            )
        )

    def _record_project_audit(
        self,
        action: str,
        project: Project,
        summary: str,
        after_data: dict[str, Any],
    ) -> None:
        self.audit_logs.create(
            AuditLogCreate(
                company_id=project.company_id,
                action=action,
                target_type="project",
                target_id=project.id,
                summary=summary,
                after_data_json=after_data,
            )
        )
