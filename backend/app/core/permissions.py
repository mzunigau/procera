from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.request_context import RequestContext, get_request_context
from app.modules.roles.permissions import Permission, permissions_for_role_names
from app.modules.roles.repository import RoleRepository, UserRoleRepository


def permissions_for_context(context: RequestContext, db: Session) -> set[str]:
    if context.is_development_context:
        return {permission.value for permission in Permission}
    if context.user_id is None:
        return set()

    role_repository = RoleRepository(db)
    user_role_repository = UserRoleRepository(db)
    role_links = user_role_repository.list(company_id=context.company_id, user_id=context.user_id)
    role_names = []
    for role_link in role_links:
        role = role_repository.get(role_link.role_id)
        if role is not None:
            role_names.append(role.name)
    return set(permissions_for_role_names(role_names))


def require_permission(permission: Permission):
    def dependency(
        context: RequestContext = Depends(get_request_context),
        db: Session = Depends(get_db),
    ) -> RequestContext:
        permissions = permissions_for_context(context, db)
        if permission.value not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Permission required",
                    "permission": permission.value,
                },
            )
        return context

    return dependency
