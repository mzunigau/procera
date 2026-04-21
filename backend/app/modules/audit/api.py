from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.audit.schemas import AuditLogRead
from app.modules.audit.service import AuditLogService


router = APIRouter(prefix="/audit-logs", tags=["audit"])


def get_audit_log_service(db: Session = Depends(get_db)) -> AuditLogService:
    return AuditLogService(db)


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    company_id: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    service: AuditLogService = Depends(get_audit_log_service),
    context: RequestContext = Depends(require_permission(Permission.AUDIT_VIEW)),
):
    return service.list_audit_logs(
        company_id=context.company_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
    )


@router.get("/{audit_log_id}", response_model=AuditLogRead)
def get_audit_log(
    audit_log_id: str,
    service: AuditLogService = Depends(get_audit_log_service),
    context: RequestContext = Depends(require_permission(Permission.AUDIT_VIEW)),
):
    audit_log = service.get_audit_log(audit_log_id)
    ensure_company_access(audit_log, context)
    return audit_log
