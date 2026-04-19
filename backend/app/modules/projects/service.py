from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.process_steps.repository import ProcessStepRepository
from app.modules.processes.repository import ProcessRepository
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.repository = ProjectRepository(db)
        self.process_repository = ProcessRepository(db)
        self.process_step_repository = ProcessStepRepository(db)
        self.task_repository = TaskRepository(db)

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
        if data.process_id is not None:
            self._ensure_process_matches_company(data.process_id, data.company_id)

        project = self.repository.create(data)
        if data.process_id is not None:
            self._generate_tasks_from_process(project, data.process_id)
        return project

    def update_project(self, project_id: str, data: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        return self.repository.update(project, data)

    def delete_project(self, project_id: str) -> None:
        project = self.get_project(project_id)
        self.repository.delete(project)

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

    def _generate_tasks_from_process(self, project: Project, process_id: str) -> None:
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
                )
            )
