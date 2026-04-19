from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task, TaskAttachment, TaskComment
from app.modules.tasks.schemas import (
    TaskAttachmentCreate,
    TaskAttachmentUpdate,
    TaskCommentCreate,
    TaskCommentUpdate,
    TaskCreate,
    TaskUpdate,
)


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        project_id: str | None = None,
    ) -> list[Task]:
        query = select(Task).order_by(Task.created_at.desc())
        if company_id:
            query = query.where(Task.company_id == company_id)
        if project_id:
            query = query.where(Task.project_id == project_id)
        return list(self.db.scalars(query).all())

    def get(self, task_id: str) -> Task | None:
        return self.db.get(Task, task_id)

    def create(self, data: TaskCreate) -> Task:
        task = Task(**data.model_dump(exclude={"assigned_to"}))
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task: Task, data: TaskUpdate) -> Task:
        values = data.model_dump(exclude_unset=True, exclude={"assigned_to"})
        for field, value in values.items():
            setattr(task, field, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.commit()


class TaskAttachmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        task_id: str | None = None,
    ) -> list[TaskAttachment]:
        query = select(TaskAttachment).order_by(TaskAttachment.created_at.desc())
        if company_id:
            query = query.where(TaskAttachment.company_id == company_id)
        if task_id:
            query = query.where(TaskAttachment.task_id == task_id)
        return list(self.db.scalars(query).all())

    def get(self, attachment_id: str) -> TaskAttachment | None:
        return self.db.get(TaskAttachment, attachment_id)

    def create(self, data: TaskAttachmentCreate) -> TaskAttachment:
        attachment = TaskAttachment(**data.model_dump())
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def update(
        self,
        attachment: TaskAttachment,
        data: TaskAttachmentUpdate,
    ) -> TaskAttachment:
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(attachment, field, value)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def delete(self, attachment: TaskAttachment) -> None:
        self.db.delete(attachment)
        self.db.commit()


class TaskCommentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        task_id: str | None = None,
    ) -> list[TaskComment]:
        query = select(TaskComment).order_by(TaskComment.created_at.asc())
        if company_id:
            query = query.where(TaskComment.company_id == company_id)
        if task_id:
            query = query.where(TaskComment.task_id == task_id)
        return list(self.db.scalars(query).all())

    def get(self, comment_id: str) -> TaskComment | None:
        return self.db.get(TaskComment, comment_id)

    def create(self, data: TaskCommentCreate) -> TaskComment:
        comment = TaskComment(**data.model_dump())
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def update(self, comment: TaskComment, data: TaskCommentUpdate) -> TaskComment:
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(comment, field, value)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete(self, comment: TaskComment) -> None:
        self.db.delete(comment)
        self.db.commit()
