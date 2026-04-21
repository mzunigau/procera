from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.projects.models import Project, ProjectProcessInstance
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectProcessInstanceCreate,
    ProjectProcessInstanceUpdate,
    ProjectUpdate,
)


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, company_id: str | None = None) -> list[Project]:
        query = select(Project).order_by(Project.created_at.desc())
        if company_id:
            query = query.where(Project.company_id == company_id)
        return list(self.db.scalars(query).all())

    def get(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)

    def create(self, data: ProjectCreate, commit: bool = True) -> Project:
        project = Project(**data.model_dump(exclude={"process_id"}))
        self.db.add(project)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(project)
        return project

    def update(self, project: Project, data: ProjectUpdate) -> Project:
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(project, field, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()


class ProjectProcessInstanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        project_id: str | None = None,
    ) -> list[ProjectProcessInstance]:
        query = select(ProjectProcessInstance).order_by(
            ProjectProcessInstance.created_at.desc(),
        )
        if company_id:
            query = query.where(ProjectProcessInstance.company_id == company_id)
        if project_id:
            query = query.where(ProjectProcessInstance.project_id == project_id)
        return list(self.db.scalars(query).all())

    def get(self, instance_id: str) -> ProjectProcessInstance | None:
        return self.db.get(ProjectProcessInstance, instance_id)

    def create(
        self,
        project_id: str,
        data: ProjectProcessInstanceCreate,
        commit: bool = True,
    ) -> ProjectProcessInstance:
        instance = ProjectProcessInstance(
            project_id=project_id,
            **data.model_dump(),
        )
        self.db.add(instance)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(instance)
        return instance

    def update(
        self,
        instance: ProjectProcessInstance,
        data: ProjectProcessInstanceUpdate,
        commit: bool = True,
    ) -> ProjectProcessInstance:
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(instance, field, value)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(instance)
        return instance
