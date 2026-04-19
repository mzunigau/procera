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
    app.include_router(projects_router)
    app.include_router(processes_router)
    app.include_router(process_steps_router)
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


def test_process_step_and_instruction_crud() -> None:
    with build_client() as client:
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Employee Onboarding",
                "code": "HR-ONB",
                "objective": "Guide new employee onboarding.",
                "scope": "HR and administration",
                "status": "draft",
            },
        )
        assert process_response.status_code == 201
        process = process_response.json()
        process_id = process["id"]

        updated_process = client.patch(
            f"/processes/{process_id}",
            json={"status": "published", "version_label": "v1"},
        )
        assert updated_process.status_code == 200
        assert updated_process.json()["status"] == "published"

        step_response = client.post(
            f"/processes/{process_id}/steps",
            json={
                "company_id": "company-1",
                "process_id": process_id,
                "step_order": 1,
                "name": "Collect employee documents",
                "description": "Request required onboarding records.",
                "instruction_summary": "Confirm all required files are received.",
                "expected_duration_hours": 4,
                "sla_hours": 24,
                "requires_evidence": True,
                "requires_approval": False,
            },
        )
        assert step_response.status_code == 201
        step = step_response.json()
        assert step["process_id"] == process_id
        assert step["step_order"] == 1

        step_id = step["id"]
        updated_step = client.patch(
            f"/process-steps/{step_id}",
            json={"requires_approval": True},
        )
        assert updated_step.status_code == 200
        assert updated_step.json()["requires_approval"] is True

        instruction_response = client.post(
            f"/process-steps/{step_id}/instructions",
            json={
                "company_id": "company-1",
                "process_step_id": step_id,
                "title": "Required records",
                "content_markdown": "Collect identification and signed forms.",
            },
        )
        assert instruction_response.status_code == 201
        instruction = instruction_response.json()
        assert instruction["process_step_id"] == step_id

        instruction_id = instruction["id"]
        listed_instructions = client.get(
            "/process-step-instructions",
            params={"process_step_id": step_id},
        )
        assert listed_instructions.status_code == 200
        assert len(listed_instructions.json()) == 1

        updated_instruction = client.patch(
            f"/process-step-instructions/{instruction_id}",
            json={"title": "Required onboarding records"},
        )
        assert updated_instruction.status_code == 200
        assert updated_instruction.json()["title"] == "Required onboarding records"

        assert client.delete(f"/process-step-instructions/{instruction_id}").status_code == 204
        assert client.delete(f"/process-steps/{step_id}").status_code == 204
        assert client.delete(f"/processes/{process_id}").status_code == 204


def test_process_step_requires_existing_process_in_same_company() -> None:
    with build_client() as client:
        created = client.post(
            "/processes/missing-process/steps",
            json={
                "company_id": "company-1",
                "process_id": "missing-process",
                "step_order": 1,
                "name": "Invalid step",
            },
        )
        assert created.status_code == 400
        assert created.json()["detail"]["message"] == "Process does not exist"
