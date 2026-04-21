from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository


class ReferenceValidator:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def ensure_user_matches_company(
        self,
        user_id: str | None,
        company_id: str,
        field_name: str,
    ) -> None:
        if user_id is None:
            return

        user = self.users.get(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": f"{field_name} does not reference an existing user"},
            )
        if user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": f"{field_name} belongs to a different company"},
            )

    def ensure_role_matches_company(
        self,
        role_id: str | None,
        company_id: str,
        field_name: str,
    ) -> None:
        if role_id is None:
            return

        role = self.roles.get(role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": f"{field_name} does not reference an existing role"},
            )
        if role.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": f"{field_name} belongs to a different company"},
            )
