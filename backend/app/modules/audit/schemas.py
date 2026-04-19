from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    company_id: str
    actor_user_id: str | None = None
    action: str = Field(min_length=1, max_length=100)
    target_type: str = Field(min_length=1, max_length=100)
    target_id: str
    summary: str = Field(min_length=1)
    before_data_json: dict | None = None
    after_data_json: dict | None = None


class AuditLogRead(AuditLogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
