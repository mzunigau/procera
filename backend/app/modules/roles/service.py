from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.roles.models import Role, UserRole
from app.modules.roles.permissions import permissions_for_role_names
from app.modules.roles.repository import RoleRepository, UserRoleRepository
from app.modules.roles.schemas import RoleCreate, RoleUpdate, UserRoleCreate
from app.modules.users.repository import UserRepository


class RoleService:
    def __init__(self, db: Session) -> None:
        self.roles = RoleRepository(db)
        self.user_roles = UserRoleRepository(db)
        self.users = UserRepository(db)

    def list_roles(self, company_id: str | None = None) -> list[Role]:
        return self.roles.list(company_id=company_id)

    def get_role(self, role_id: str) -> Role:
        role = self.roles.get(role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Role not found"},
            )
        return role

    def create_role(self, data: RoleCreate) -> Role:
        if self.roles.get_by_name(data.company_id, data.name) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Role name already exists for this company"},
            )
        return self.roles.create(data)

    def update_role(self, role_id: str, data: RoleUpdate) -> Role:
        role = self.get_role(role_id)
        if data.name is not None:
            existing_role = self.roles.get_by_name(role.company_id, data.name)
            if existing_role is not None and existing_role.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Role name already exists for this company"},
                )
        return self.roles.update(role, data)

    def delete_role(self, role_id: str) -> None:
        role = self.get_role(role_id)
        self.roles.delete(role)

    def list_user_roles(
        self,
        company_id: str | None = None,
        user_id: str | None = None,
        role_id: str | None = None,
    ) -> list[UserRole]:
        return self.user_roles.list(company_id=company_id, user_id=user_id, role_id=role_id)

    def assign_role_to_user(self, data: UserRoleCreate) -> UserRole:
        user = self.users.get(data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User does not exist"},
            )
        role = self.roles.get(data.role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Role does not exist"},
            )
        if user.company_id != data.company_id or role.company_id != data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User and role must belong to the same company"},
            )

        existing_assignment = self.user_roles.get_assignment(
            data.company_id,
            data.user_id,
            data.role_id,
        )
        if existing_assignment is not None:
            return existing_assignment

        return self.user_roles.create(data)

    def remove_user_role(self, user_role_id: str) -> None:
        user_role = self.user_roles.get(user_role_id)
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "User role assignment not found"},
            )
        self.user_roles.delete(user_role)

    def get_role_permissions(self, role_id: str) -> list[str]:
        role = self.get_role(role_id)
        return permissions_for_role_names([role.name])
