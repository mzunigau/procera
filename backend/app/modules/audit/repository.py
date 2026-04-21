from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogCreate


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        action: str | None = None,
    ) -> list[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.created_at.asc())
        if company_id:
            query = query.where(AuditLog.company_id == company_id)
        if target_type:
            query = query.where(AuditLog.target_type == target_type)
        if target_id:
            query = query.where(AuditLog.target_id == target_id)
        if action:
            query = query.where(AuditLog.action == action)
        return list(self.db.scalars(query).all())

    def get(self, audit_log_id: str) -> AuditLog | None:
        return self.db.get(AuditLog, audit_log_id)

    def create(self, data: AuditLogCreate, commit: bool = True) -> AuditLog:
        audit_log = AuditLog(**data.model_dump())
        self.db.add(audit_log)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(audit_log)
        return audit_log
