from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.models import Role, UserRole
from app.modules.roles.schemas import RoleCreate, RoleUpdate, UserRoleCreate


class RoleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, company_id: str | None = None) -> list[Role]:
        query = select(Role).order_by(Role.created_at.desc())
        if company_id:
            query = query.where(Role.company_id == company_id)
        return list(self.db.scalars(query).all())

    def get(self, role_id: str) -> Role | None:
        return self.db.get(Role, role_id)

    def get_by_name(self, company_id: str, name: str) -> Role | None:
        query = select(Role).where(Role.company_id == company_id, Role.name == name)
        return self.db.scalars(query).first()

    def create(self, data: RoleCreate) -> Role:
        role = Role(**data.model_dump())
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update(self, role: Role, data: RoleUpdate) -> Role:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role: Role) -> None:
        self.db.delete(role)
        self.db.commit()


class UserRoleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        user_id: str | None = None,
        role_id: str | None = None,
    ) -> list[UserRole]:
        query = select(UserRole).order_by(UserRole.created_at.desc())
        if company_id:
            query = query.where(UserRole.company_id == company_id)
        if user_id:
            query = query.where(UserRole.user_id == user_id)
        if role_id:
            query = query.where(UserRole.role_id == role_id)
        return list(self.db.scalars(query).all())

    def get(self, user_role_id: str) -> UserRole | None:
        return self.db.get(UserRole, user_role_id)

    def get_assignment(self, company_id: str, user_id: str, role_id: str) -> UserRole | None:
        query = select(UserRole).where(
            UserRole.company_id == company_id,
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        return self.db.scalars(query).first()

    def create(self, data: UserRoleCreate) -> UserRole:
        user_role = UserRole(**data.model_dump())
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role

    def delete(self, user_role: UserRole) -> None:
        self.db.delete(user_role)
        self.db.commit()
