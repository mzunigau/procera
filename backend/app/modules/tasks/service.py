import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.audit.schemas import AuditLogCreate
from app.modules.audit.service import AuditLogService
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.models import Task, TaskAttachment, TaskComment, TaskStatus
from app.modules.tasks.repository import (
    TaskAttachmentRepository,
    TaskCommentRepository,
    TaskRepository,
)
from app.modules.tasks.schemas import (
    TaskAttachmentCreate,
    TaskAttachmentUpdate,
    TaskCommentCreate,
    TaskCommentUpdate,
    TaskCreate,
    TaskUpdate,
)


ALLOWED_TASK_STATUS_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.COMPLETED, TaskStatus.BLOCKED},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.BLOCKED},
    TaskStatus.BLOCKED: {TaskStatus.PENDING, TaskStatus.IN_PROGRESS},
    TaskStatus.COMPLETED: set(),
}


class TaskService:
    def __init__(self, db: Session) -> None:
        self.repository = TaskRepository(db)
        self.attachment_repository = TaskAttachmentRepository(db)
        self.comment_repository = TaskCommentRepository(db)
        self.project_repository = ProjectRepository(db)
        self.audit_log_service = AuditLogService(db)

    def list_tasks(
        self,
        company_id: str | None = None,
        project_id: str | None = None,
    ) -> list[Task]:
        return self.repository.list(company_id=company_id, project_id=project_id)

    def get_task(self, task_id: str) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Task not found"},
            )
        return task

    def create_task(self, data: TaskCreate) -> Task:
        self._ensure_project_exists(data.project_id)
        self._apply_assigned_to(data)
        task = self.repository.create(data)
        self.audit_log_service.record(
            AuditLogCreate(
                company_id=task.company_id,
                action="task.created",
                target_type="task",
                target_id=task.id,
                summary=f"Task created: {task.title}",
                after_data_json=self._task_audit_data(task),
            )
        )
        return task

    def update_task(self, task_id: str, data: TaskUpdate) -> Task:
        task = self.get_task(task_id)
        before_data = self._task_audit_data(task)
        if data.project_id is not None:
            self._ensure_project_exists(data.project_id)
        if data.status is not None:
            self._validate_status_transition(task.status, data.status)
        self._apply_assigned_to(data)
        updated_task = self.repository.update(task, data)
        after_data = self._task_audit_data(updated_task)
        self._record_task_update_audit(updated_task, data, before_data, after_data)
        return updated_task

    def delete_task(self, task_id: str) -> None:
        task = self.get_task(task_id)
        self.repository.delete(task)

    def list_task_attachments(
        self,
        task_id: str | None = None,
        company_id: str | None = None,
    ) -> list[TaskAttachment]:
        if task_id is not None:
            self.get_task(task_id)
        return self.attachment_repository.list(company_id=company_id, task_id=task_id)

    def get_task_attachment(self, attachment_id: str) -> TaskAttachment:
        attachment = self.attachment_repository.get(attachment_id)
        if attachment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Task attachment not found"},
            )
        return attachment

    def create_task_attachment(
        self,
        task_id: str,
        data: TaskAttachmentCreate,
    ) -> TaskAttachment:
        task = self.get_task(task_id)
        if task.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Task belongs to a different company"},
            )
        data.task_id = task_id
        return self.attachment_repository.create(data)

    def upload_task_attachment(
        self,
        task_id: str,
        company_id: str,
        uploaded_by_user_id: str | None,
        file: UploadFile,
    ) -> TaskAttachment:
        task = self.get_task(task_id)
        if task.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Task belongs to a different company"},
            )

        upload_dir = Path(settings.upload_storage_path) / "task_attachments" / task_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_name = file.filename or "attachment"
        storage_file_name = f"{uuid.uuid4()}_{Path(file_name).name}"
        storage_path = upload_dir / storage_file_name
        with storage_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        return self.attachment_repository.create(
            TaskAttachmentCreate(
                company_id=company_id,
                task_id=task_id,
                file_name=file_name,
                storage_key=str(storage_path),
                content_type=file.content_type,
                size_bytes=storage_path.stat().st_size,
                uploaded_by_user_id=uploaded_by_user_id,
            )
        )

    def update_task_attachment(
        self,
        attachment_id: str,
        data: TaskAttachmentUpdate,
    ) -> TaskAttachment:
        attachment = self.get_task_attachment(attachment_id)
        return self.attachment_repository.update(attachment, data)

    def delete_task_attachment(self, attachment_id: str) -> None:
        attachment = self.get_task_attachment(attachment_id)
        self.attachment_repository.delete(attachment)

    def list_task_comments(
        self,
        task_id: str | None = None,
        company_id: str | None = None,
    ) -> list[TaskComment]:
        if task_id is not None:
            self.get_task(task_id)
        return self.comment_repository.list(company_id=company_id, task_id=task_id)

    def get_task_comment(self, comment_id: str) -> TaskComment:
        comment = self.comment_repository.get(comment_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Task comment not found"},
            )
        return comment

    def create_task_comment(
        self,
        task_id: str,
        data: TaskCommentCreate,
    ) -> TaskComment:
        task = self.get_task(task_id)
        if task.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Task belongs to a different company"},
            )
        data.task_id = task_id
        return self.comment_repository.create(data)

    def update_task_comment(
        self,
        comment_id: str,
        data: TaskCommentUpdate,
    ) -> TaskComment:
        comment = self.get_task_comment(comment_id)
        return self.comment_repository.update(comment, data)

    def delete_task_comment(self, comment_id: str) -> None:
        comment = self.get_task_comment(comment_id)
        self.comment_repository.delete(comment)

    def _ensure_project_exists(self, project_id: str) -> None:
        if self.project_repository.get(project_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Project does not exist"},
            )

    def _apply_assigned_to(self, data: TaskCreate | TaskUpdate) -> None:
        if "assigned_to" not in data.model_fields_set:
            return
        if data.assigned_to is None:
            data.assignee_user_id = None
            data.assignee_role_id = None
            return
        if data.assigned_to.type == "user":
            data.assignee_user_id = data.assigned_to.id
            data.assignee_role_id = None
            return
        data.assignee_user_id = None
        data.assignee_role_id = data.assigned_to.id

    def _validate_status_transition(
        self,
        current_status: TaskStatus,
        next_status: TaskStatus,
    ) -> None:
        if current_status == next_status:
            return
        allowed_statuses = ALLOWED_TASK_STATUS_TRANSITIONS[current_status]
        if next_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid task status transition",
                    "current_status": current_status,
                    "next_status": next_status,
                    "allowed_statuses": sorted(allowed_statuses),
                },
            )

    def _record_task_update_audit(
        self,
        task: Task,
        data: TaskUpdate,
        before_data: dict,
        after_data: dict,
    ) -> None:
        changed_fields = [
            field
            for field in after_data
            if before_data.get(field) != after_data.get(field)
        ]
        if not changed_fields:
            return

        if "status" in changed_fields:
            self.audit_log_service.record(
                AuditLogCreate(
                    company_id=task.company_id,
                    action="task.status_changed",
                    target_type="task",
                    target_id=task.id,
                    summary=(
                        "Task status changed from "
                        f"{before_data['status']} to {after_data['status']}"
                    ),
                    before_data_json={"status": before_data["status"]},
                    after_data_json={"status": after_data["status"]},
                )
            )

        edited_fields = [field for field in changed_fields if field != "status"]
        if edited_fields:
            self.audit_log_service.record(
                AuditLogCreate(
                    company_id=task.company_id,
                    action="task.updated",
                    target_type="task",
                    target_id=task.id,
                    summary=f"Task updated: {', '.join(edited_fields)}",
                    before_data_json={
                        field: before_data.get(field) for field in edited_fields
                    },
                    after_data_json={
                        field: after_data.get(field) for field in edited_fields
                    },
                )
            )

    def _task_audit_data(self, task: Task) -> dict:
        return {
            "id": task.id,
            "company_id": task.company_id,
            "project_id": task.project_id,
            "process_step_id": task.process_step_id,
            "parent_task_id": task.parent_task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "assignee_user_id": task.assignee_user_id,
            "assignee_role_id": task.assignee_role_id,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "requires_evidence": task.requires_evidence,
            "requires_approval": task.requires_approval,
        }
