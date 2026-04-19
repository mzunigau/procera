from collections.abc import Generator
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.process_steps.api import router as process_steps_router
from app.modules.processes.api import router as processes_router
from app.modules.projects.api import router as projects_router
from app.modules.tasks.api import router as tasks_router


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
    app.include_router(processes_router)
    app.include_router(process_steps_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)

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


def test_project_crud() -> None:
    with build_client() as client:
        created = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Implementation Project",
                "code": "PRJ-001",
                "description": "Base project",
                "objective": "Validate project CRUD",
                "status": "draft",
            },
        )
        assert created.status_code == 201
        project = created.json()
        assert project["name"] == "Implementation Project"
        assert project["status"] == "draft"

        project_id = project["id"]
        fetched = client.get(f"/projects/{project_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == project_id

        updated = client.patch(f"/projects/{project_id}", json={"status": "active"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "active"

        listed = client.get("/projects", params={"company_id": "company-1"})
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        deleted = client.delete(f"/projects/{project_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/projects/{project_id}")
        assert missing.status_code == 404


def test_project_created_from_process_generates_tasks_from_process_steps() -> None:
    with build_client() as client:
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Supplier Onboarding",
                "status": "published",
            },
        )
        assert process_response.status_code == 201
        process_id = process_response.json()["id"]

        first_step = client.post(
            f"/processes/{process_id}/steps",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "step_order": 1,
                "name": "Collect supplier documents",
                "description": "Request required supplier records.",
                "responsible_user_id": "user-1",
                "requires_evidence": True,
                "requires_approval": False,
            },
        )
        assert first_step.status_code == 201

        second_step = client.post(
            f"/processes/{process_id}/steps",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "step_order": 2,
                "name": "Review supplier documents",
                "description": "Check submitted supplier records.",
                "responsible_role_id": "role-reviewer",
                "requires_evidence": False,
                "requires_approval": True,
            },
        )
        assert second_step.status_code == 201

        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Onboard supplier ACME",
                "status": "active",
                "process_id": process_id,
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        tasks_response = client.get("/tasks", params={"project_id": project_id})
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        assert len(tasks) == 2

        tasks_by_title = {task["title"]: task for task in tasks}
        collect_task = tasks_by_title["Collect supplier documents"]
        review_task = tasks_by_title["Review supplier documents"]

        assert collect_task["process_step_id"] == first_step.json()["id"]
        assert collect_task["assignee_user_id"] == "user-1"
        assert collect_task["requires_evidence"] is True
        assert collect_task["requires_approval"] is False

        assert review_task["process_step_id"] == second_step.json()["id"]
        assert review_task["assignee_role_id"] == "role-reviewer"
        assert review_task["requires_evidence"] is False
        assert review_task["requires_approval"] is True


def test_project_created_from_process_requires_existing_process_in_same_company() -> None:
    with build_client() as client:
        created = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Invalid process project",
                "process_id": "missing-process",
            },
        )
        assert created.status_code == 400
        assert created.json()["detail"]["message"] == "Process does not exist"
