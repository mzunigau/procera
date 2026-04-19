from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.documents.models import DocumentStatus, DocumentVersionStatus


class DocumentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    document_type: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    owner_user_id: str | None = None
    status: DocumentStatus = DocumentStatus.DRAFT


class DocumentCreate(DocumentBase):
    company_id: str


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    owner_user_id: str | None = None
    status: DocumentStatus | None = None
    current_version_id: str | None = None


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    current_version_id: str | None
    created_at: datetime
    updated_at: datetime


class DocumentVersionBase(BaseModel):
    version_number: int = Field(ge=1)
    file_name: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=500)
    content_type: str | None = Field(default=None, max_length=100)
    size_bytes: int = Field(ge=0)
    change_summary: str | None = None
    status: DocumentVersionStatus = DocumentVersionStatus.DRAFT
    created_by_user_id: str | None = None
    approved_by_user_id: str | None = None
    approved_at: datetime | None = None


class DocumentVersionCreate(DocumentVersionBase):
    company_id: str
    document_id: str


class DocumentVersionRead(DocumentVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    document_id: str
    created_at: datetime


class DocumentLinkBase(BaseModel):
    linked_type: str = Field(min_length=1, max_length=100)
    linked_id: str
    relation_type: str = Field(min_length=1, max_length=100)


class DocumentLinkCreate(DocumentLinkBase):
    company_id: str
    document_id: str | None = None


class DocumentLinkRead(DocumentLinkBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    document_id: str
    created_at: datetime


class DocumentUploadRead(BaseModel):
    document: DocumentRead
    version: DocumentVersionRead
    link: DocumentLinkRead | None = None
