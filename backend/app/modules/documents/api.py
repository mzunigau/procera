from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentLinkRead,
    DocumentRead,
    DocumentUpdate,
    DocumentUploadRead,
    DocumentVersionRead,
)
from app.modules.documents.service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


@router.get("", response_model=list[DocumentRead])
def list_documents(
    company_id: str | None = Query(default=None),
    service: DocumentService = Depends(get_document_service),
):
    return service.list_documents(company_id=company_id)


@router.get("/links/by-target", response_model=list[DocumentLinkRead])
def list_document_links_by_target(
    linked_type: str = Query(...),
    linked_id: str = Query(...),
    service: DocumentService = Depends(get_document_service),
):
    return service.list_document_links(linked_type=linked_type, linked_id=linked_id)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    data: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
):
    return service.create_document(data)


@router.post("/upload", response_model=DocumentUploadRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    company_id: str = Form(...),
    title: str = Form(...),
    document_type: str = Form(...),
    category: str | None = Form(default=None),
    owner_user_id: str | None = Form(default=None),
    created_by_user_id: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    linked_type: str | None = Form(default=None),
    linked_id: str | None = Form(default=None),
    relation_type: str | None = Form(default=None),
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    return service.upload_document(
        company_id=company_id,
        title=title,
        document_type=document_type,
        category=category,
        owner_user_id=owner_user_id,
        created_by_user_id=created_by_user_id,
        change_summary=change_summary,
        linked_type=linked_type,
        linked_id=linked_id,
        relation_type=relation_type,
        file=file,
    )


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    return service.get_document(document_id)


@router.patch("/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: str,
    data: DocumentUpdate,
    service: DocumentService = Depends(get_document_service),
):
    return service.update_document(document_id, data)


@router.get("/{document_id}/versions", response_model=list[DocumentVersionRead])
def list_document_versions(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    return service.list_document_versions(document_id)


@router.post(
    "/{document_id}/versions/upload",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_document_version(
    document_id: str,
    company_id: str = Form(...),
    created_by_user_id: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    return service.upload_document_version(
        document_id=document_id,
        company_id=company_id,
        created_by_user_id=created_by_user_id,
        change_summary=change_summary,
        file=file,
    )


@router.get("/{document_id}/links", response_model=list[DocumentLinkRead])
def list_document_links(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    return service.list_document_links(document_id=document_id)


@router.post("/{document_id}/links", response_model=DocumentLinkRead, status_code=status.HTTP_201_CREATED)
def link_document(
    document_id: str,
    data: DocumentLinkCreate,
    service: DocumentService = Depends(get_document_service),
):
    data.document_id = document_id
    return service.link_document(data)
