import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.reference_validation import ReferenceValidator
from app.modules.documents.models import Document
from app.modules.documents.repository import (
    DocumentLinkRepository,
    DocumentRepository,
    DocumentVersionRepository,
)
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentUpdate,
    DocumentUploadRead,
    DocumentVersionCreate,
)
from app.modules.process_steps.repository import ProcessStepRepository
from app.modules.processes.repository import ProcessRepository
from app.modules.tasks.repository import TaskRepository


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.documents = DocumentRepository(db)
        self.versions = DocumentVersionRepository(db)
        self.links = DocumentLinkRepository(db)
        self.processes = ProcessRepository(db)
        self.process_steps = ProcessStepRepository(db)
        self.tasks = TaskRepository(db)
        self.reference_validator = ReferenceValidator(db)

    def list_documents(self, company_id: str | None = None) -> list[Document]:
        return self.documents.list(company_id=company_id)

    def get_document(self, document_id: str) -> Document:
        document = self.documents.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Document not found"},
            )
        return document

    def create_document(self, data: DocumentCreate) -> Document:
        self.reference_validator.ensure_user_matches_company(
            data.owner_user_id,
            data.company_id,
            "owner_user_id",
        )
        return self.documents.create(data)

    def update_document(self, document_id: str, data: DocumentUpdate) -> Document:
        document = self.get_document(document_id)
        if "owner_user_id" in data.model_fields_set:
            self.reference_validator.ensure_user_matches_company(
                data.owner_user_id,
                document.company_id,
                "owner_user_id",
            )
        return self.documents.update(document, data)

    def list_document_versions(self, document_id: str):
        self.get_document(document_id)
        return self.versions.list(document_id=document_id)

    def upload_document_version(
        self,
        document_id: str,
        company_id: str,
        created_by_user_id: str | None,
        change_summary: str | None,
        file: UploadFile,
    ):
        document = self.get_document(document_id)
        if document.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Document belongs to a different company"},
            )
        self.reference_validator.ensure_user_matches_company(
            created_by_user_id,
            company_id,
            "created_by_user_id",
        )

        upload_dir = Path(settings.upload_storage_path) / "documents" / document.id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_name = file.filename or "document"
        storage_file_name = f"{uuid.uuid4()}_{Path(file_name).name}"
        storage_path = upload_dir / storage_file_name
        with storage_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        version = self.versions.create(
            DocumentVersionCreate(
                company_id=company_id,
                document_id=document.id,
                version_number=self.versions.next_version_number(document.id),
                file_name=file_name,
                storage_key=str(storage_path),
                content_type=file.content_type,
                size_bytes=storage_path.stat().st_size,
                change_summary=change_summary,
                created_by_user_id=created_by_user_id,
            )
        )
        self.documents.update(document, DocumentUpdate(current_version_id=version.id))
        return version

    def list_document_links(
        self,
        company_id: str | None = None,
        document_id: str | None = None,
        linked_type: str | None = None,
        linked_id: str | None = None,
    ):
        if document_id:
            self.get_document(document_id)
        return self.links.list(
            company_id=company_id,
            document_id=document_id,
            linked_type=linked_type,
            linked_id=linked_id,
        )

    def link_document(self, data: DocumentLinkCreate):
        if data.document_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "document_id is required"},
            )
        document = self.get_document(data.document_id)
        if document.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Document belongs to a different company"},
            )
        self._ensure_link_target_matches_company(data.linked_type, data.linked_id, data.company_id)
        return self.links.create(data)

    def upload_document(
        self,
        company_id: str,
        title: str,
        document_type: str,
        category: str | None,
        owner_user_id: str | None,
        created_by_user_id: str | None,
        change_summary: str | None,
        linked_type: str | None,
        linked_id: str | None,
        relation_type: str | None,
        file: UploadFile,
    ) -> DocumentUploadRead:
        if linked_type or linked_id or relation_type:
            if not linked_type or not linked_id or not relation_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "linked_type, linked_id, and relation_type are required together"},
                )
            self._ensure_link_target_matches_company(linked_type, linked_id, company_id)
        self.reference_validator.ensure_user_matches_company(
            owner_user_id,
            company_id,
            "owner_user_id",
        )
        self.reference_validator.ensure_user_matches_company(
            created_by_user_id,
            company_id,
            "created_by_user_id",
        )

        document = self.documents.create(
            DocumentCreate(
                company_id=company_id,
                title=title,
                document_type=document_type,
                category=category,
                owner_user_id=owner_user_id,
            )
        )

        upload_dir = Path(settings.upload_storage_path) / "documents" / document.id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_name = file.filename or "document"
        storage_file_name = f"{uuid.uuid4()}_{Path(file_name).name}"
        storage_path = upload_dir / storage_file_name
        with storage_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        version = self.versions.create(
            DocumentVersionCreate(
                company_id=company_id,
                document_id=document.id,
                version_number=1,
                file_name=file_name,
                storage_key=str(storage_path),
                content_type=file.content_type,
                size_bytes=storage_path.stat().st_size,
                change_summary=change_summary,
                created_by_user_id=created_by_user_id,
            )
        )
        document = self.documents.update(
            document,
            DocumentUpdate(current_version_id=version.id),
        )

        link = None
        if linked_type and linked_id and relation_type:
            link = self.links.create(
                DocumentLinkCreate(
                    company_id=company_id,
                    document_id=document.id,
                    linked_type=linked_type,
                    linked_id=linked_id,
                    relation_type=relation_type,
                )
            )

        return DocumentUploadRead(document=document, version=version, link=link)

    def _ensure_link_target_matches_company(
        self,
        linked_type: str,
        linked_id: str,
        company_id: str,
    ) -> None:
        if linked_type == "process":
            target = self.processes.get(linked_id)
        elif linked_type == "process_step":
            target = self.process_steps.get(linked_id)
        elif linked_type == "task":
            target = self.tasks.get(linked_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "linked_type must be process, process_step, or task"},
            )

        if target is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Linked target does not exist"},
            )
        if target.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Linked target belongs to a different company"},
            )
