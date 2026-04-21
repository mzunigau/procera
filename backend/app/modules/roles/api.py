from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.roles.schemas import RoleCreate, RoleRead, RoleUpdate, UserRoleCreate, UserRoleRead
from app.modules.roles.service import RoleService


router = APIRouter(tags=["roles"])


def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    return RoleService(db)


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    company_id: str | None = Query(default=None),
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    return service.list_roles(company_id=context.company_id)


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    data.company_id = context.company_id
    return service.create_role(data)


@router.get("/roles/{role_id}", response_model=RoleRead)
def get_role(
    role_id: str,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    role = service.get_role(role_id)
    ensure_company_access(role, context)
    return role


@router.patch("/roles/{role_id}", response_model=RoleRead)
def update_role(
    role_id: str,
    data: RoleUpdate,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    ensure_company_access(service.get_role(role_id), context)
    return service.update_role(role_id, data)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: str,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    ensure_company_access(service.get_role(role_id), context)
    service.delete_role(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/roles/{role_id}/permissions", response_model=list[str])
def get_role_permissions(
    role_id: str,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    ensure_company_access(service.get_role(role_id), context)
    return service.get_role_permissions(role_id)


@router.get("/user-roles", response_model=list[UserRoleRead])
def list_user_roles(
    company_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    role_id: str | None = Query(default=None),
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    return service.list_user_roles(company_id=context.company_id, user_id=user_id, role_id=role_id)


@router.post("/user-roles", response_model=UserRoleRead, status_code=status.HTTP_201_CREATED)
def assign_role_to_user(
    data: UserRoleCreate,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    data.company_id = context.company_id
    return service.assign_role_to_user(data)


@router.delete("/user-roles/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_role(
    user_role_id: str,
    service: RoleService = Depends(get_role_service),
    context: RequestContext = Depends(require_permission(Permission.ROLE_MANAGE)),
):
    user_role = service.user_roles.get(user_role_id)
    if user_role is not None:
        ensure_company_access(user_role, context)
    service.remove_user_role(user_role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
