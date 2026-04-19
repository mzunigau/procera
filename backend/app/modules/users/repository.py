from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, company_id: str | None = None) -> list[User]:
        query = select(User).order_by(User.created_at.desc())
        if company_id:
            query = query.where(User.company_id == company_id)
        return list(self.db.scalars(query).all())

    def get(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, company_id: str, email: str) -> User | None:
        query = select(User).where(User.company_id == company_id, User.email == email)
        return self.db.scalars(query).first()

    def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
