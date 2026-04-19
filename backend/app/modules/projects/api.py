from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.projects.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from app.modules.projects.service import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    company_id: str | None = Query(default=None),
    service: ProjectService = Depends(get_project_service),
):
    return service.list_projects(company_id=company_id)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
):
    return service.create_project(data)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    return service.get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
):
    return service.update_project(project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
