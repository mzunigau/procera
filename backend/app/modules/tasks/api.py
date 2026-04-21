from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.tasks.schemas import (
    TaskAttachmentCreate,
    TaskAttachmentRead,
    TaskAttachmentUpdate,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCommentUpdate,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.modules.tasks.service import TaskService


router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)


@router.get("", response_model=list[TaskRead])
def list_tasks(
    company_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_VIEW)),
):
    return service.list_tasks(company_id=context.company_id, project_id=project_id)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    data.company_id = context.company_id
    return service.create_task(data)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_VIEW)),
):
    task = service.get_task(task_id)
    ensure_company_access(task, context)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str,
    data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    ensure_company_access(service.get_task(task_id), context)
    return service.update_task(task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    ensure_company_access(service.get_task(task_id), context)
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{task_id}/attachments", response_model=list[TaskAttachmentRead])
def list_task_attachments(
    task_id: str,
    company_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_VIEW)),
):
    ensure_company_access(service.get_task(task_id), context)
    return service.list_task_attachments(task_id=task_id, company_id=context.company_id)


@router.post(
    "/{task_id}/attachments",
    response_model=TaskAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task_attachment_reference(
    task_id: str,
    data: TaskAttachmentCreate,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    data.company_id = context.company_id
    if context.user_id is not None:
        data.uploaded_by_user_id = context.user_id
    return service.create_task_attachment(task_id, data)


@router.post(
    "/{task_id}/attachments/upload",
    response_model=TaskAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_task_attachment(
    task_id: str,
    company_id: str | None = Form(default=None),
    uploaded_by_user_id: str | None = Form(default=None),
    file: UploadFile = File(...),
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    return service.upload_task_attachment(
        task_id=task_id,
        company_id=context.company_id,
        uploaded_by_user_id=context.user_id or uploaded_by_user_id,
        file=file,
    )


@router.get("/attachments/{attachment_id}", response_model=TaskAttachmentRead)
def get_task_attachment(
    attachment_id: str,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_VIEW)),
):
    attachment = service.get_task_attachment(attachment_id)
    ensure_company_access(attachment, context)
    return attachment


@router.patch("/attachments/{attachment_id}", response_model=TaskAttachmentRead)
def update_task_attachment(
    attachment_id: str,
    data: TaskAttachmentUpdate,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    ensure_company_access(service.get_task_attachment(attachment_id), context)
    if context.user_id is not None:
        data.uploaded_by_user_id = context.user_id
    return service.update_task_attachment(attachment_id, data)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_attachment(
    attachment_id: str,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    ensure_company_access(service.get_task_attachment(attachment_id), context)
    service.delete_task_attachment(attachment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{task_id}/comments", response_model=list[TaskCommentRead])
def list_task_comments(
    task_id: str,
    company_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_VIEW)),
):
    ensure_company_access(service.get_task(task_id), context)
    return service.list_task_comments(task_id=task_id, company_id=context.company_id)


@router.post(
    "/{task_id}/comments",
    response_model=TaskCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task_comment(
    task_id: str,
    data: TaskCommentCreate,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    data.company_id = context.company_id
    if context.user_id is not None:
        data.author_user_id = context.user_id
    return service.create_task_comment(task_id, data)


@router.get("/comments/{comment_id}", response_model=TaskCommentRead)
def get_task_comment(
    comment_id: str,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_VIEW)),
):
    comment = service.get_task_comment(comment_id)
    ensure_company_access(comment, context)
    return comment


@router.patch("/comments/{comment_id}", response_model=TaskCommentRead)
def update_task_comment(
    comment_id: str,
    data: TaskCommentUpdate,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    ensure_company_access(service.get_task_comment(comment_id), context)
    if context.user_id is not None:
        data.author_user_id = context.user_id
    return service.update_task_comment(comment_id, data)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_comment(
    comment_id: str,
    service: TaskService = Depends(get_task_service),
    context: RequestContext = Depends(require_permission(Permission.TASK_MANAGE)),
):
    ensure_company_access(service.get_task_comment(comment_id), context)
    service.delete_task_comment(comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
