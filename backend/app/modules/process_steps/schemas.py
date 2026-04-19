from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProcessStepBase(BaseModel):
    step_order: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    responsible_role_id: str | None = None
    responsible_user_id: str | None = None
    instruction_summary: str | None = None
    expected_duration_hours: int | None = Field(default=None, ge=0)
    sla_hours: int | None = Field(default=None, ge=0)
    requires_evidence: bool = False
    requires_approval: bool = False


class ProcessStepCreate(ProcessStepBase):
    company_id: str
    process_id: str


class ProcessStepUpdate(BaseModel):
    process_id: str | None = None
    step_order: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    responsible_role_id: str | None = None
    responsible_user_id: str | None = None
    instruction_summary: str | None = None
    expected_duration_hours: int | None = Field(default=None, ge=0)
    sla_hours: int | None = Field(default=None, ge=0)
    requires_evidence: bool | None = None
    requires_approval: bool | None = None


class ProcessStepRead(ProcessStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    process_id: str
    created_at: datetime
    updated_at: datetime


class ProcessStepInstructionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_markdown: str = Field(min_length=1)


class ProcessStepInstructionCreate(ProcessStepInstructionBase):
    company_id: str
    process_step_id: str


class ProcessStepInstructionUpdate(BaseModel):
    process_step_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content_markdown: str | None = Field(default=None, min_length=1)


class ProcessStepInstructionRead(ProcessStepInstructionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    process_step_id: str
    created_at: datetime
    updated_at: datetime
