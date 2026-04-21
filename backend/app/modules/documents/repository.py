from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.documents.models import Document, DocumentLink, DocumentVersion
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentUpdate,
    DocumentVersionCreate,
)


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, company_id: str | None = None) -> list[Document]:
        query = select(Document).order_by(Document.created_at.desc())
        if company_id:
            query = query.where(Document.company_id == company_id)
        return list(self.db.scalars(query).all())

    def get(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

    def create(self, data: DocumentCreate) -> Document:
        document = Document(**data.model_dump())
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: Document, data: DocumentUpdate) -> Document:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(document, field, value)
        self.db.commit()
        self.db.refresh(document)
        return document


class DocumentVersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, document_id: str | None = None) -> list[DocumentVersion]:
        query = select(DocumentVersion).order_by(DocumentVersion.version_number.desc())
        if document_id:
            query = query.where(DocumentVersion.document_id == document_id)
        return list(self.db.scalars(query).all())

    def next_version_number(self, document_id: str) -> int:
        versions = self.list(document_id=document_id)
        if not versions:
            return 1
        return versions[0].version_number + 1

    def create(self, data: DocumentVersionCreate) -> DocumentVersion:
        version = DocumentVersion(**data.model_dump())
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version


class DocumentLinkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        document_id: str | None = None,
        linked_type: str | None = None,
        linked_id: str | None = None,
    ) -> list[DocumentLink]:
        query = select(DocumentLink).order_by(DocumentLink.created_at.desc())
        if company_id:
            query = query.where(DocumentLink.company_id == company_id)
        if document_id:
            query = query.where(DocumentLink.document_id == document_id)
        if linked_type:
            query = query.where(DocumentLink.linked_type == linked_type)
        if linked_id:
            query = query.where(DocumentLink.linked_id == linked_id)
        return list(self.db.scalars(query).all())

    def create(self, data: DocumentLinkCreate) -> DocumentLink:
        link = DocumentLink(**data.model_dump())
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link
