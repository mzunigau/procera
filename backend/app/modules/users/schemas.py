from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.models import UserStatus


class UserBase(BaseModel):
    company_id: str
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    status: UserStatus = UserStatus.INVITED


class UserCreate(UserBase):
    password_hash: str = Field(min_length=1, max_length=255)


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    password_hash: str | None = Field(default=None, min_length=1, max_length=255)
    status: UserStatus | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class UserPermissionsRead(BaseModel):
    user_id: str
    company_id: str
    roles: list[str]
    permissions: list[str]
