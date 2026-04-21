from collections.abc import Generator
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.audit.api import router as audit_router
from app.modules.projects.api import router as projects_router
from app.modules.roles.api import router as roles_router
from app.modules.tasks.api import router as tasks_router
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
    app.include_router(projects_router)
    app.include_router(tasks_router)
    app.include_router(audit_router)
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


def create_user(client: TestClient, email: str) -> dict:
    response = client.post(
        "/users",
        json={
            "company_id": "company-1",
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password_hash": "hashed-password",
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()


def assign_role(client: TestClient, user_id: str, role_name: str) -> None:
    role_response = client.post(
        "/roles",
        json={
            "company_id": "company-1",
            "name": role_name,
        },
    )
    assert role_response.status_code == 201

    assignment_response = client.post(
        "/user-roles",
        json={
            "company_id": "company-1",
            "user_id": user_id,
            "role_id": role_response.json()["id"],
        },
    )
    assert assignment_response.status_code == 201


def test_authenticated_user_without_role_is_denied_sensitive_endpoint() -> None:
    with build_client() as client:
        user = create_user(client, "no-role@example.com")

        response = client.post(
            "/projects",
            headers={"X-Procera-User-Id": user["id"]},
            json={
                "company_id": "company-1",
                "name": "Unauthorized project",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"]["permission"] == "project:manage"


def test_authenticated_project_manager_can_manage_projects_and_tasks() -> None:
    with build_client() as client:
        user = create_user(client, "manager@example.com")
        assign_role(client, user["id"], "Project Manager")
        headers = {"X-Procera-User-Id": user["id"]}

        project_response = client.post(
            "/projects",
            headers=headers,
            json={
                "company_id": "company-1",
                "name": "Authorized project",
            },
        )
        assert project_response.status_code == 201

        task_response = client.post(
            "/tasks",
            headers=headers,
            json={
                "company_id": "company-1",
                "project_id": project_response.json()["id"],
                "title": "Authorized task",
            },
        )
        assert task_response.status_code == 201


def test_project_manager_cannot_view_audit_logs_without_audit_permission() -> None:
    with build_client() as client:
        user = create_user(client, "audit-denied@example.com")
        assign_role(client, user["id"], "Project Manager")

        response = client.get(
            "/audit-logs",
            headers={"X-Procera-User-Id": user["id"]},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["permission"] == "audit:view"


def test_auditor_can_view_audit_logs() -> None:
    with build_client() as client:
        user = create_user(client, "auditor@example.com")
        assign_role(client, user["id"], "Auditor")

        response = client.get(
            "/audit-logs",
            headers={"X-Procera-User-Id": user["id"]},
        )

        assert response.status_code == 200
