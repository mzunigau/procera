from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.processes.models import ProcessStatus


class ProcessBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    objective: str | None = None
    scope: str | None = None
    owner_user_id: str | None = None
    version_label: str | None = Field(default=None, max_length=50)
    status: ProcessStatus = ProcessStatus.DRAFT


class ProcessCreate(ProcessBase):
    company_id: str


class ProcessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    objective: str | None = None
    scope: str | None = None
    owner_user_id: str | None = None
    version_label: str | None = Field(default=None, max_length=50)
    status: ProcessStatus | None = None


class ProcessRead(ProcessBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
