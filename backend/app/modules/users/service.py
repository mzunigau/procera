from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.roles.permissions import permissions_for_role_names
from app.modules.roles.repository import RoleRepository, UserRoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserPermissionsRead, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.user_roles = UserRoleRepository(db)

    def list_users(self, company_id: str | None = None) -> list[User]:
        return self.users.list(company_id=company_id)

    def get_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "User not found"},
            )
        return user

    def create_user(self, data: UserCreate) -> User:
        if self.users.get_by_email(data.company_id, data.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User email already exists for this company"},
            )
        return self.users.create(data)

    def update_user(self, user_id: str, data: UserUpdate) -> User:
        user = self.get_user(user_id)
        if data.email is not None:
            existing_user = self.users.get_by_email(user.company_id, data.email)
            if existing_user is not None and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "User email already exists for this company"},
                )
        return self.users.update(user, data)

    def delete_user(self, user_id: str) -> None:
        user = self.get_user(user_id)
        self.users.delete(user)

    def get_permissions(self, user_id: str, company_id: str | None = None) -> UserPermissionsRead:
        user = self.get_user(user_id)
        if company_id is not None and user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User belongs to a different company"},
            )

        role_links = self.user_roles.list(company_id=user.company_id, user_id=user_id)
        role_names = []
        for role_link in role_links:
            role = self.roles.get(role_link.role_id)
            if role is not None:
                role_names.append(role.name)

        return UserPermissionsRead(
            user_id=user.id,
            company_id=user.company_id,
            roles=sorted(role_names),
            permissions=permissions_for_role_names(role_names),
        )
