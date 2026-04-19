from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    company_id: str
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class RoleRead(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class UserRoleCreate(BaseModel):
    company_id: str
    user_id: str
    role_id: str


class UserRoleRead(UserRoleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
