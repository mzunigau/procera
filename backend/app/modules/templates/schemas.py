from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.models import ProjectStatus
from app.modules.templates.models import TemplateType


class TemplateBase(BaseModel):
    company_id: str
    template_type: TemplateType
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    payload_json: dict[str, Any]


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    payload_json: dict[str, Any] | None = None


class TemplateRead(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class TemplateFromSourceCreate(BaseModel):
    company_id: str
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectFromTemplateCreate(BaseModel):
    company_id: str
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None
    objective: str | None = None
    status: ProjectStatus = ProjectStatus.DRAFT
    start_date: date | None = None
    due_date: date | None = None
    owner_user_id: str | None = None
