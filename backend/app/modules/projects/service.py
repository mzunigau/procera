from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.reference_validation import ReferenceValidator
from app.modules.audit.repository import AuditLogRepository
from app.modules.audit.schemas import AuditLogCreate
from app.modules.process_steps.repository import ProcessStepRepository
from app.modules.processes.repository import ProcessRepository
from app.modules.projects.models import Project, ProjectProcessInstance, ProjectProcessInstanceStatus
from app.modules.projects.repository import ProjectProcessInstanceRepository, ProjectRepository
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectProcessInstanceCreate,
    ProjectProcessInstanceUpdate,
    ProjectUpdate,
)
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ProjectRepository(db)
        self.process_repository = ProcessRepository(db)
        self.process_step_repository = ProcessStepRepository(db)
        self.task_repository = TaskRepository(db)
        self.process_instance_repository = ProjectProcessInstanceRepository(db)
        self.audit_logs = AuditLogRepository(db)
        self.reference_validator = ReferenceValidator(db)

    def list_projects(self, company_id: str | None = None) -> list[Project]:
        return self.repository.list(company_id=company_id)

    def get_project(self, project_id: str) -> Project:
        project = self.repository.get(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Project not found"},
            )
        return project

    def create_project(self, data: ProjectCreate) -> Project:
        self.reference_validator.ensure_user_matches_company(
            data.owner_user_id,
            data.company_id,
            "owner_user_id",
        )
        if data.process_id is not None:
            self._ensure_process_matches_company(data.process_id, data.company_id)

        if data.process_id is None:
            try:
                project = self.repository.create(data, commit=False)
                self._record_audit(
                    "project.created",
                    project.company_id,
                    "project",
                    project.id,
                    f"Project created: {project.name}",
                    after_data=self._project_audit_data(project),
                    commit=False,
                )
                self.db.commit()
                self.db.refresh(project)
                return project
            except Exception:
                self.db.rollback()
                raise

        try:
            project = self.repository.create(data, commit=False)
            self._record_audit(
                "project.created",
                project.company_id,
                "project",
                project.id,
                f"Project created: {project.name}",
                after_data=self._project_audit_data(project),
                commit=False,
            )
            instance = self._create_process_instance(
                project=project,
                process_id=data.process_id,
                status=ProjectProcessInstanceStatus.ACTIVE,
                started_at=datetime.now(UTC),
                commit=False,
            )
            self._generate_tasks_from_process_instance(instance, commit=False)
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception:
            self.db.rollback()
            raise

    def update_project(self, project_id: str, data: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        before_data = self._project_audit_data(project)
        if "owner_user_id" in data.model_fields_set:
            self.reference_validator.ensure_user_matches_company(
                data.owner_user_id,
                project.company_id,
                "owner_user_id",
            )
        updated = self.repository.update(project, data)
        after_data = self._project_audit_data(updated)
        changed_fields = [
            field for field in after_data if before_data.get(field) != after_data.get(field)
        ]
        if changed_fields:
            self._record_audit(
                "project.updated",
                updated.company_id,
                "project",
                updated.id,
                f"Project updated: {', '.join(changed_fields)}",
                before_data={field: before_data.get(field) for field in changed_fields},
                after_data={field: after_data.get(field) for field in changed_fields},
            )
        return updated

    def delete_project(self, project_id: str) -> None:
        project = self.get_project(project_id)
        self.repository.delete(project)

    def list_process_instances(
        self,
        project_id: str,
        company_id: str | None = None,
    ) -> list[ProjectProcessInstance]:
        self.get_project(project_id)
        return self.process_instance_repository.list(
            company_id=company_id,
            project_id=project_id,
        )

    def get_process_instance(self, instance_id: str) -> ProjectProcessInstance:
        instance = self.process_instance_repository.get(instance_id)
        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Project process instance not found"},
            )
        return instance

    def create_process_instance(
        self,
        project_id: str,
        data: ProjectProcessInstanceCreate,
    ) -> ProjectProcessInstance:
        project = self.get_project(project_id)
        if project.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Project belongs to a different company"},
            )
        self._ensure_process_matches_company(data.process_id, data.company_id)
        return self._create_process_instance(
            project=project,
            process_id=data.process_id,
            name=data.name,
            status=data.status,
            started_at=data.started_at,
            completed_at=data.completed_at,
        )

    def generate_tasks_from_process_instance(
        self,
        instance_id: str,
    ) -> ProjectProcessInstance:
        instance = self.get_process_instance(instance_id)
        if instance.status != ProjectProcessInstanceStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process instance has already generated tasks"},
            )

        try:
            self._generate_tasks_from_process_instance(instance, commit=False)
            updated = self.process_instance_repository.update(
                instance,
                ProjectProcessInstanceUpdate(
                    status=ProjectProcessInstanceStatus.ACTIVE,
                    started_at=instance.started_at or datetime.now(UTC),
                ),
                commit=False,
            )
            self._record_audit(
                "project_process_instance.tasks_generated",
                instance.company_id,
                "project_process_instance",
                instance.id,
                f"Tasks generated from process instance: {instance.name}",
                after_data=self._process_instance_audit_data(updated),
                commit=False,
            )
            self.db.commit()
            self.db.refresh(updated)
            return updated
        except Exception:
            self.db.rollback()
            raise

    def _ensure_process_matches_company(self, process_id: str, company_id: str) -> None:
        process = self.process_repository.get(process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process does not exist"},
            )
        if process.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process belongs to a different company"},
            )

    def _generate_tasks_from_process(
        self,
        project: Project,
        process_id: str,
        commit: bool = True,
    ) -> None:
        process_steps = self.process_step_repository.list(
            company_id=project.company_id,
            process_id=process_id,
        )
        for process_step in process_steps:
            self.task_repository.create(
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
                ),
                commit=commit,
            )

    def _create_process_instance(
        self,
        project: Project,
        process_id: str,
        name: str | None = None,
        status: ProjectProcessInstanceStatus = ProjectProcessInstanceStatus.PENDING,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        commit: bool = True,
    ) -> ProjectProcessInstance:
        process = self.process_repository.get(process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process does not exist"},
            )
        if process.company_id != project.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process belongs to a different company"},
            )
        data = ProjectProcessInstanceCreate(
            company_id=project.company_id,
            process_id=process_id,
            name=name or process.name,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
        )
        if not commit:
            instance = self.process_instance_repository.create(project.id, data, commit=False)
            self._record_audit(
                "project_process_instance.created",
                instance.company_id,
                "project_process_instance",
                instance.id,
                f"Process instance created: {instance.name}",
                after_data=self._process_instance_audit_data(instance),
                commit=False,
            )
            return instance

        try:
            instance = self.process_instance_repository.create(project.id, data, commit=False)
            self._record_audit(
                "project_process_instance.created",
                instance.company_id,
                "project_process_instance",
                instance.id,
                f"Process instance created: {instance.name}",
                after_data=self._process_instance_audit_data(instance),
                commit=False,
            )
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except Exception:
            self.db.rollback()
            raise

    def _generate_tasks_from_process_instance(
        self,
        instance: ProjectProcessInstance,
        commit: bool = True,
    ) -> None:
        project = self.get_project(instance.project_id)
        if project.company_id != instance.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process instance belongs to a different company"},
            )
        self._generate_tasks_from_process(project, instance.process_id, commit=commit)

    def _record_audit(
        self,
        action: str,
        company_id: str,
        target_type: str,
        target_id: str,
        summary: str,
        before_data: dict[str, Any] | None = None,
        after_data: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> None:
        self.audit_logs.create(
            AuditLogCreate(
                company_id=company_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                summary=summary,
                before_data_json=before_data,
                after_data_json=after_data,
            ),
            commit=commit,
        )

    def _project_audit_data(self, project: Project) -> dict[str, Any]:
        return {
            "id": project.id,
            "company_id": project.company_id,
            "name": project.name,
            "code": project.code,
            "description": project.description,
            "objective": project.objective,
            "status": project.status.value,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "owner_user_id": project.owner_user_id,
        }

    def _process_instance_audit_data(
        self,
        instance: ProjectProcessInstance,
    ) -> dict[str, Any]:
        return {
            "id": instance.id,
            "company_id": instance.company_id,
            "project_id": instance.project_id,
            "process_id": instance.process_id,
            "name": instance.name,
            "status": instance.status.value,
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
        }
