from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.projects.schemas import ProjectRead
from app.modules.templates.models import TemplateType
from app.modules.templates.schemas import (
    ProjectFromTemplateCreate,
    TemplateCreate,
    TemplateFromSourceCreate,
    TemplateRead,
    TemplateUpdate,
)
from app.modules.templates.service import TemplateService


router = APIRouter(prefix="/templates", tags=["templates"])


def get_template_service(db: Session = Depends(get_db)) -> TemplateService:
    return TemplateService(db)


@router.get("", response_model=list[TemplateRead])
def list_templates(
    company_id: str | None = Query(default=None),
    template_type: TemplateType | None = Query(default=None),
    service: TemplateService = Depends(get_template_service),
):
    return service.list_templates(company_id=company_id, template_type=template_type)


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(
    data: TemplateCreate,
    service: TemplateService = Depends(get_template_service),
):
    return service.create_template(data)


@router.post(
    "/from-process/{process_id}",
    response_model=TemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_template_from_process(
    process_id: str,
    data: TemplateFromSourceCreate,
    service: TemplateService = Depends(get_template_service),
):
    return service.create_from_process(process_id, data)


@router.post(
    "/from-project/{project_id}",
    response_model=TemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_template_from_project(
    project_id: str,
    data: TemplateFromSourceCreate,
    service: TemplateService = Depends(get_template_service),
):
    return service.create_from_project(project_id, data)


@router.get("/{template_id}", response_model=TemplateRead)
def get_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service),
):
    return service.get_template(template_id)


@router.patch("/{template_id}", response_model=TemplateRead)
def update_template(
    template_id: str,
    data: TemplateUpdate,
    service: TemplateService = Depends(get_template_service),
):
    return service.update_template(template_id, data)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service),
):
    service.delete_template(template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{template_id}/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_from_template(
    template_id: str,
    data: ProjectFromTemplateCreate,
    service: TemplateService = Depends(get_template_service),
):
    return service.create_project_from_template(template_id, data)
