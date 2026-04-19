from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate


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

    def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump(exclude={"process_id"}))
        self.db.add(project)
        self.db.commit()
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
