from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.users.schemas import UserCreate, UserPermissionsRead, UserRead, UserUpdate
from app.modules.users.service import UserService


router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("", response_model=list[UserRead])
def list_users(
    company_id: str | None = Query(default=None),
    service: UserService = Depends(get_user_service),
    context: RequestContext = Depends(require_permission(Permission.USER_MANAGE)),
):
    return service.list_users(company_id=context.company_id)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
    context: RequestContext = Depends(require_permission(Permission.USER_MANAGE)),
):
    data.company_id = context.company_id
    return service.create_user(data)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    context: RequestContext = Depends(require_permission(Permission.USER_MANAGE)),
):
    user = service.get_user(user_id)
    ensure_company_access(user, context)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
    context: RequestContext = Depends(require_permission(Permission.USER_MANAGE)),
):
    ensure_company_access(service.get_user(user_id), context)
    return service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    context: RequestContext = Depends(require_permission(Permission.USER_MANAGE)),
):
    ensure_company_access(service.get_user(user_id), context)
    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/permissions", response_model=UserPermissionsRead)
def get_user_permissions(
    user_id: str,
    company_id: str | None = Query(default=None),
    service: UserService = Depends(get_user_service),
    context: RequestContext = Depends(get_request_context),
):
    return service.get_permissions(user_id=user_id, company_id=context.company_id)
