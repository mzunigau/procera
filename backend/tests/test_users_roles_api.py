from collections.abc import Generator
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.roles.api import router as roles_router
from app.modules.users.api import router as users_router


@contextmanager
def build_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    app = FastAPI()
    app.include_router(users_router)
    app.include_router(roles_router)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def test_user_role_assignment_and_permissions() -> None:
    with build_client() as client:
        user_response = client.post(
            "/users",
            json={
                "company_id": "company-1",
                "first_name": "Alicia",
                "last_name": "Mora",
                "email": "alicia@example.com",
                "password_hash": "hashed-password",
                "status": "active",
            },
        )
        assert user_response.status_code == 201
        user = user_response.json()
        assert "password_hash" not in user

        role_response = client.post(
            "/roles",
            json={
                "company_id": "company-1",
                "name": "Project Manager",
                "description": "Manages operational projects",
            },
        )
        assert role_response.status_code == 201
        role = role_response.json()

        assignment_response = client.post(
            "/user-roles",
            json={
                "company_id": "company-1",
                "user_id": user["id"],
                "role_id": role["id"],
            },
        )
        assert assignment_response.status_code == 201
        assignment = assignment_response.json()
        assert assignment["user_id"] == user["id"]
        assert assignment["role_id"] == role["id"]

        permissions_response = client.get(f"/users/{user['id']}/permissions")
        assert permissions_response.status_code == 200
        permissions = permissions_response.json()
        assert permissions["roles"] == ["Project Manager"]
        assert "project:manage" in permissions["permissions"]
        assert "task:manage" in permissions["permissions"]


def test_user_role_assignment_requires_same_company() -> None:
    with build_client() as client:
        user_response = client.post(
            "/users",
            json={
                "company_id": "company-1",
                "first_name": "Diego",
                "last_name": "Rojas",
                "email": "diego@example.com",
                "password_hash": "hashed-password",
            },
        )
        assert user_response.status_code == 201

        role_response = client.post(
            "/roles",
            headers={"X-Procera-Company-Id": "company-2"},
            json={
                "company_id": "company-2",
                "name": "Auditor",
            },
        )
        assert role_response.status_code == 201

        assignment_response = client.post(
            "/user-roles",
            json={
                "company_id": "company-1",
                "user_id": user_response.json()["id"],
                "role_id": role_response.json()["id"],
            },
        )
        assert assignment_response.status_code == 400
        assert assignment_response.json()["detail"]["message"] == "User and role must belong to the same company"


def test_user_and_role_crud() -> None:
    with build_client() as client:
        user_response = client.post(
            "/users",
            json={
                "company_id": "company-1",
                "first_name": "Mariana",
                "last_name": "Solano",
                "email": "mariana@example.com",
                "password_hash": "hashed-password",
            },
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        updated_user = client.patch(f"/users/{user_id}", json={"status": "active"})
        assert updated_user.status_code == 200
        assert updated_user.json()["status"] == "active"

        role_response = client.post(
            "/roles",
            json={
                "company_id": "company-1",
                "name": "Reviewer",
            },
        )
        assert role_response.status_code == 201
        role_id = role_response.json()["id"]

        role_permissions = client.get(f"/roles/{role_id}/permissions")
        assert role_permissions.status_code == 200
        assert "task:review" in role_permissions.json()

        listed_users = client.get("/users", params={"company_id": "company-1"})
        assert listed_users.status_code == 200
        assert len(listed_users.json()) == 1

        listed_roles = client.get("/roles", params={"company_id": "company-1"})
        assert listed_roles.status_code == 200
        assert len(listed_roles.json()) == 1

        assert client.delete(f"/roles/{role_id}").status_code == 204
        assert client.delete(f"/users/{user_id}").status_code == 204
