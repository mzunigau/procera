from collections.abc import Generator
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.audit.api import router as audit_router
from app.modules.process_steps.api import router as process_steps_router
from app.modules.processes.api import router as processes_router
from app.modules.projects.api import (
    project_process_instances_router,
    router as projects_router,
)
from app.modules.roles.api import router as roles_router
from app.modules.tasks.api import router as tasks_router
from app.modules.tasks.repository import TaskRepository
from app.modules.users.api import router as users_router


@contextmanager
def build_client(
    raise_server_exceptions: bool = True,
) -> Generator[TestClient, None, None]:
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
    app.include_router(project_process_instances_router)
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
        with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def create_user(client: TestClient, email: str = "person@example.com") -> str:
    response = client.post(
        "/users",
        json={
            "company_id": "company-1",
            "first_name": "Procera",
            "last_name": "User",
            "email": email,
            "password_hash": "hash",
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_role(client: TestClient, name: str = "Reviewer") -> str:
    response = client.post(
        "/roles",
        json={
            "company_id": "company-1",
            "name": name,
            "description": "Test role",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


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

        created_audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "project",
                "target_id": project_id,
                "action": "project.created",
            },
        )
        assert created_audit_logs.status_code == 200
        assert len(created_audit_logs.json()) == 1
        assert created_audit_logs.json()[0]["after_data_json"]["name"] == (
            "Implementation Project"
        )

        updated_audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "project",
                "target_id": project_id,
                "action": "project.updated",
            },
        )
        assert updated_audit_logs.status_code == 200
        assert len(updated_audit_logs.json()) == 1
        assert updated_audit_logs.json()[0]["before_data_json"] == {"status": "draft"}
        assert updated_audit_logs.json()[0]["after_data_json"] == {"status": "active"}

        listed = client.get("/projects", params={"company_id": "company-1"})
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        deleted = client.delete(f"/projects/{project_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/projects/{project_id}")
        assert missing.status_code == 404


def test_project_created_from_process_generates_tasks_from_process_steps() -> None:
    with build_client() as client:
        user_id = create_user(client)
        role_id = create_role(client)
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
                "responsible_user_id": user_id,
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
                "responsible_role_id": role_id,
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

        instances_response = client.get(f"/projects/{project_id}/process-instances")
        assert instances_response.status_code == 200
        instances = instances_response.json()
        assert len(instances) == 1
        assert instances[0]["project_id"] == project_id
        assert instances[0]["process_id"] == process_id
        assert instances[0]["status"] == "active"

        instance_audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "project_process_instance",
                "target_id": instances[0]["id"],
                "action": "project_process_instance.created",
            },
        )
        assert instance_audit_logs.status_code == 200
        assert len(instance_audit_logs.json()) == 1

        tasks_response = client.get("/tasks", params={"project_id": project_id})
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        assert len(tasks) == 2

        tasks_by_title = {task["title"]: task for task in tasks}
        collect_task = tasks_by_title["Collect supplier documents"]
        review_task = tasks_by_title["Review supplier documents"]

        assert collect_task["process_step_id"] == first_step.json()["id"]
        assert collect_task["assignee_user_id"] == user_id
        assert collect_task["requires_evidence"] is True
        assert collect_task["requires_approval"] is False

        assert review_task["process_step_id"] == second_step.json()["id"]
        assert review_task["assignee_role_id"] == role_id
        assert review_task["requires_evidence"] is False
        assert review_task["requires_approval"] is True


def test_project_process_instance_generates_tasks_on_demand() -> None:
    with build_client() as client:
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Corrective Action",
                "status": "published",
            },
        )
        assert process_response.status_code == 201
        process_id = process_response.json()["id"]

        step_response = client.post(
            f"/processes/{process_id}/steps",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "step_order": 1,
                "name": "Contain issue",
                "requires_evidence": True,
            },
        )
        assert step_response.status_code == 201

        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "CAPA-001",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        instance_response = client.post(
            f"/projects/{project_id}/process-instances",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "name": "CAPA workflow",
            },
        )
        assert instance_response.status_code == 201
        instance = instance_response.json()
        assert instance["status"] == "pending"

        generated_response = client.post(
            f"/project-process-instances/{instance['id']}/generate-tasks",
        )
        assert generated_response.status_code == 200
        assert generated_response.json()["status"] == "active"
        assert generated_response.json()["started_at"] is not None

        generated_audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "project_process_instance",
                "target_id": instance["id"],
                "action": "project_process_instance.tasks_generated",
            },
        )
        assert generated_audit_logs.status_code == 200
        assert len(generated_audit_logs.json()) == 1

        tasks_response = client.get("/tasks", params={"project_id": project_id})
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Contain issue"
        assert tasks[0]["process_step_id"] == step_response.json()["id"]

        duplicate_response = client.post(
            f"/project-process-instances/{instance['id']}/generate-tasks",
        )
        assert duplicate_response.status_code == 400
        assert duplicate_response.json()["detail"]["message"] == (
            "Process instance has already generated tasks"
        )


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


def test_process_step_rejects_missing_responsible_role_reference() -> None:
    with build_client() as client:
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Reference validation process",
                "status": "published",
            },
        )
        assert process_response.status_code == 201
        process_id = process_response.json()["id"]

        step_response = client.post(
            f"/processes/{process_id}/steps",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "step_order": 1,
                "name": "Step with missing role",
                "responsible_role_id": "missing-role",
            },
        )
        assert step_response.status_code == 400
        assert step_response.json()["detail"]["message"] == (
            "responsible_role_id does not reference an existing role"
        )


def test_project_created_from_process_rolls_back_when_task_generation_fails(
    monkeypatch,
) -> None:
    original_create = TaskRepository.create

    def fail_task_creation(self, data, commit=True):
        if data.title == "Explode":
            raise RuntimeError("task generation failed")
        return original_create(self, data, commit=commit)

    monkeypatch.setattr(TaskRepository, "create", fail_task_creation)

    with build_client(raise_server_exceptions=False) as client:
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Rollback Process",
                "status": "published",
            },
        )
        assert process_response.status_code == 201
        process_id = process_response.json()["id"]

        step_response = client.post(
            f"/processes/{process_id}/steps",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "step_order": 1,
                "name": "Explode",
            },
        )
        assert step_response.status_code == 201

        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Project that should roll back",
                "process_id": process_id,
            },
        )
        assert project_response.status_code == 500

        projects_response = client.get("/projects")
        assert projects_response.status_code == 200
        assert projects_response.json() == []
