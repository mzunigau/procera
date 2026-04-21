from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectProcessInstanceCreate,
    ProjectProcessInstanceRead,
    ProjectRead,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])
project_process_instances_router = APIRouter(
    prefix="/project-process-instances",
    tags=["project-process-instances"],
)


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_VIEW)),
):
    return service.list_projects(company_id=context.company_id)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_MANAGE)),
):
    data.company_id = context.company_id
    return service.create_project(data)


@router.get(
    "/{project_id}/process-instances",
    response_model=list[ProjectProcessInstanceRead],
)
def list_project_process_instances(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_VIEW)),
):
    ensure_company_access(service.get_project(project_id), context)
    return service.list_process_instances(project_id, company_id=context.company_id)


@router.post(
    "/{project_id}/process-instances",
    response_model=ProjectProcessInstanceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project_process_instance(
    project_id: str,
    data: ProjectProcessInstanceCreate,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_MANAGE)),
):
    ensure_company_access(service.get_project(project_id), context)
    data.company_id = context.company_id
    return service.create_process_instance(project_id, data)


@project_process_instances_router.post(
    "/{instance_id}/generate-tasks",
    response_model=ProjectProcessInstanceRead,
)
def generate_tasks_from_project_process_instance(
    instance_id: str,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_MANAGE)),
):
    instance = service.get_process_instance(instance_id)
    ensure_company_access(instance, context)
    return service.generate_tasks_from_process_instance(instance_id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_VIEW)),
):
    project = service.get_project(project_id)
    ensure_company_access(project, context)
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_MANAGE)),
):
    ensure_company_access(service.get_project(project_id), context)
    return service.update_project(project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    context: RequestContext = Depends(require_permission(Permission.PROJECT_MANAGE)),
):
    ensure_company_access(service.get_project(project_id), context)
    service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
