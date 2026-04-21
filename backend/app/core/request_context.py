from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


DEFAULT_DEVELOPMENT_COMPANY_ID = "company-1"


@dataclass(frozen=True)
class RequestContext:
    company_id: str
    user_id: str | None = None
    user: User | None = None
    is_development_context: bool = False


def get_request_context(
    db: Session = Depends(get_db),
    x_procera_user_id: str | None = Header(default=None, alias="X-Procera-User-Id"),
    x_procera_company_id: str | None = Header(default=None, alias="X-Procera-Company-Id"),
) -> RequestContext:
    if x_procera_user_id:
        user = UserRepository(db).get(x_procera_user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Current user does not exist"},
            )
        if x_procera_company_id is not None and x_procera_company_id != user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Current user belongs to a different company"},
            )
        return RequestContext(company_id=user.company_id, user_id=user.id, user=user)

    return RequestContext(
        company_id=x_procera_company_id or DEFAULT_DEVELOPMENT_COMPANY_ID,
        is_development_context=True,
    )


def ensure_company_access(resource: object, context: RequestContext) -> None:
    resource_company_id = getattr(resource, "company_id", None)
    if resource_company_id != context.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Resource not found"},
        )
