from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.tasks.models import TaskPriority, TaskStatus


class AssignedTo(BaseModel):
    type: Literal["user", "role"]
    id: str = Field(min_length=1)


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: AssignedTo | None = None
    assignee_user_id: str | None = None
    assignee_role_id: str | None = None
    due_date: date | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    requires_evidence: bool = False
    requires_approval: bool = False

    @model_validator(mode="after")
    def validate_assignment_input(self) -> Self:
        if self.assigned_to is not None and (
            self.assignee_user_id is not None or self.assignee_role_id is not None
        ):
            raise ValueError("Use assigned_to or assignee fields, not both")
        if self.assignee_user_id is not None and self.assignee_role_id is not None:
            raise ValueError("A task can be assigned to a user or a role, not both")
        return self


class TaskCreate(TaskBase):
    company_id: str
    project_id: str
    process_step_id: str | None = None
    parent_task_id: str | None = None


class TaskUpdate(BaseModel):
    project_id: str | None = None
    process_step_id: str | None = None
    parent_task_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assigned_to: AssignedTo | None = None
    assignee_user_id: str | None = None
    assignee_role_id: str | None = None
    due_date: date | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    requires_evidence: bool | None = None
    requires_approval: bool | None = None

    @model_validator(mode="after")
    def validate_assignment_input(self) -> Self:
        if "assigned_to" in self.model_fields_set and (
            "assignee_user_id" in self.model_fields_set
            or "assignee_role_id" in self.model_fields_set
        ):
            raise ValueError("Use assigned_to or assignee fields, not both")
        if (
            self.assignee_user_id is not None
            and self.assignee_role_id is not None
        ):
            raise ValueError("A task can be assigned to a user or a role, not both")
        return self


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str
    process_step_id: str | None
    parent_task_id: str | None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def hydrate_assigned_to(self) -> Self:
        if self.assignee_user_id is not None:
            self.assigned_to = AssignedTo(type="user", id=self.assignee_user_id)
        elif self.assignee_role_id is not None:
            self.assigned_to = AssignedTo(type="role", id=self.assignee_role_id)
        else:
            self.assigned_to = None
        return self


class TaskAttachmentBase(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=500)
    content_type: str | None = Field(default=None, max_length=100)
    size_bytes: int = Field(ge=0)
    uploaded_by_user_id: str | None = None


class TaskAttachmentCreate(TaskAttachmentBase):
    company_id: str
    task_id: str | None = None


class TaskAttachmentUpdate(BaseModel):
    file_name: str | None = Field(default=None, min_length=1, max_length=255)
    storage_key: str | None = Field(default=None, min_length=1, max_length=500)
    content_type: str | None = Field(default=None, max_length=100)
    size_bytes: int | None = Field(default=None, ge=0)
    uploaded_by_user_id: str | None = None


class TaskAttachmentRead(TaskAttachmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    task_id: str
    created_at: datetime


class TaskCommentBase(BaseModel):
    author_user_id: str | None = None
    body: str = Field(min_length=1)


class TaskCommentCreate(TaskCommentBase):
    company_id: str
    task_id: str | None = None


class TaskCommentUpdate(BaseModel):
    author_user_id: str | None = None
    body: str | None = Field(default=None, min_length=1)


class TaskCommentRead(TaskCommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    task_id: str
    created_at: datetime
    updated_at: datetime
