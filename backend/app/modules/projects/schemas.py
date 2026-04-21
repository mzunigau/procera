from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.models import ProjectProcessInstanceStatus, ProjectStatus


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None
    objective: str | None = None
    status: ProjectStatus = ProjectStatus.DRAFT
    start_date: date | None = None
    due_date: date | None = None
    owner_user_id: str | None = None


class ProjectCreate(ProjectBase):
    company_id: str
    process_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None
    objective: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    due_date: date | None = None
    owner_user_id: str | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    created_at: datetime
    updated_at: datetime


class ProjectProcessInstanceBase(BaseModel):
    process_id: str
    name: str | None = Field(default=None, max_length=255)
    status: ProjectProcessInstanceStatus = ProjectProcessInstanceStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ProjectProcessInstanceCreate(ProjectProcessInstanceBase):
    company_id: str


class ProjectProcessInstanceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: ProjectProcessInstanceStatus | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ProjectProcessInstanceRead(ProjectProcessInstanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime
