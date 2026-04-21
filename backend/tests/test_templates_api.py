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
from app.modules.roles.api import router as roles_router
from app.modules.tasks.api import router as tasks_router
from app.modules.tasks.repository import TaskRepository
from app.modules.templates.api import router as templates_router


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
    app.include_router(projects_router)
    app.include_router(processes_router)
    app.include_router(process_steps_router)
    app.include_router(tasks_router)
    app.include_router(templates_router)
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


def create_role(client: TestClient, name: str) -> str:
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


def test_process_template_can_create_project_with_generated_tasks() -> None:
    with build_client() as client:
        reviewer_role_id = create_role(client, "Purchase Reviewer")
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Purchase Approval",
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
                "name": "Review purchase request",
                "description": "Validate budget and supplier.",
                "responsible_role_id": reviewer_role_id,
                "requires_evidence": True,
                "requires_approval": True,
            },
        )
        assert step_response.status_code == 201
        source_step_id = step_response.json()["id"]

        template_response = client.post(
            f"/templates/from-process/{process_id}",
            json={
                "company_id": "company-1",
                "name": "Purchase approval template",
                "description": "Reusable purchasing workflow",
            },
        )
        assert template_response.status_code == 201
        template = template_response.json()
        assert template["template_type"] == "process"
        assert len(template["payload_json"]["steps"]) == 1

        project_response = client.post(
            f"/templates/{template['id']}/projects",
            json={
                "company_id": "company-1",
                "name": "Approve office equipment purchase",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        tasks_response = client.get("/tasks", params={"project_id": project_id})
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Review purchase request"
        assert tasks[0]["process_step_id"] != source_step_id
        assert tasks[0]["assignee_role_id"] == reviewer_role_id
        assert tasks[0]["requires_evidence"] is True
        assert tasks[0]["requires_approval"] is True


def test_project_template_can_create_project_with_task_structure() -> None:
    with build_client() as client:
        accounting_role_id = create_role(client, "Accounting")
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Monthly close",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        source_project_id = project_response.json()["id"]

        task_response = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": source_project_id,
                "title": "Reconcile bank accounts",
                "description": "Compare bank statements with ledger.",
                "status": "in_progress",
                "priority": "high",
                "assigned_to": {"type": "role", "id": accounting_role_id},
                "requires_evidence": True,
                "requires_approval": False,
            },
        )
        assert task_response.status_code == 201

        template_response = client.post(
            f"/templates/from-project/{source_project_id}",
            json={
                "company_id": "company-1",
                "name": "Monthly close template",
            },
        )
        assert template_response.status_code == 201
        template = template_response.json()
        assert template["template_type"] == "project"
        assert len(template["payload_json"]["tasks"]) == 1

        new_project_response = client.post(
            f"/templates/{template['id']}/projects",
            json={
                "company_id": "company-1",
                "name": "April close",
                "status": "active",
            },
        )
        assert new_project_response.status_code == 201
        new_project_id = new_project_response.json()["id"]

        tasks_response = client.get("/tasks", params={"project_id": new_project_id})
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Reconcile bank accounts"
        assert tasks[0]["status"] == "pending"
        assert tasks[0]["priority"] == "high"
        assert tasks[0]["assignee_role_id"] == accounting_role_id


def test_process_template_project_creation_rolls_back_partial_records(
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
                "name": "Source process",
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

        template_response = client.post(
            f"/templates/from-process/{process_id}",
            json={
                "company_id": "company-1",
                "name": "Rollback template",
            },
        )
        assert template_response.status_code == 201
        template_id = template_response.json()["id"]

        project_response = client.post(
            f"/templates/{template_id}/projects",
            json={
                "company_id": "company-1",
                "name": "Project that should roll back",
            },
        )
        assert project_response.status_code == 500

        projects_response = client.get("/projects")
        assert projects_response.status_code == 200
        assert projects_response.json() == []

        processes_response = client.get("/processes")
        assert processes_response.status_code == 200
        assert len(processes_response.json()) == 1
        assert processes_response.json()[0]["id"] == process_id
