from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditLogRepository
from app.modules.audit.schemas import AuditLogCreate


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.repository = AuditLogRepository(db)

    def list_audit_logs(
        self,
        company_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        action: str | None = None,
    ) -> list[AuditLog]:
        return self.repository.list(
            company_id=company_id,
            target_type=target_type,
            target_id=target_id,
            action=action,
        )

    def get_audit_log(self, audit_log_id: str) -> AuditLog:
        audit_log = self.repository.get(audit_log_id)
        if audit_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Audit log not found"},
            )
        return audit_log

    def record(self, data: AuditLogCreate) -> AuditLog:
        return self.repository.create(data)
