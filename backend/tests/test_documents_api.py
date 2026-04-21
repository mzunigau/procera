from collections.abc import Generator
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.modules.documents.api import router as documents_router
from app.modules.process_steps.api import router as process_steps_router
from app.modules.processes.api import router as processes_router
from app.modules.projects.api import router as projects_router
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
    original_upload_storage_path = settings.upload_storage_path
    storage_directory = TemporaryDirectory()
    object.__setattr__(settings, "upload_storage_path", storage_directory.name)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(processes_router)
    app.include_router(process_steps_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)
    app.include_router(documents_router)
    app.include_router(users_router)

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
        object.__setattr__(settings, "upload_storage_path", original_upload_storage_path)
        storage_directory.cleanup()


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


def test_document_upload_list_and_consult_linked_to_process() -> None:
    with build_client() as client:
        user_id = create_user(client)
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Documented Process",
                "status": "draft",
            },
        )
        assert process_response.status_code == 201
        process_id = process_response.json()["id"]

        uploaded = client.post(
            "/documents/upload",
            data={
                "company_id": "company-1",
                "title": "Operating Procedure",
                "document_type": "procedure",
                "category": "operations",
                "created_by_user_id": user_id,
                "change_summary": "Initial version",
                "linked_type": "process",
                "linked_id": process_id,
                "relation_type": "procedure",
            },
            files={"file": ("procedure.txt", b"procedure content", "text/plain")},
        )
        assert uploaded.status_code == 201
        payload = uploaded.json()
        document = payload["document"]
        version = payload["version"]
        link = payload["link"]
        document_id = document["id"]

        assert document["title"] == "Operating Procedure"
        assert document["current_version_id"] == version["id"]
        assert version["version_number"] == 1
        assert version["file_name"] == "procedure.txt"
        assert link["linked_type"] == "process"
        assert link["linked_id"] == process_id

        listed = client.get("/documents", params={"company_id": "company-1"})
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        fetched = client.get(f"/documents/{document_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == document_id

        versions = client.get(f"/documents/{document_id}/versions")
        assert versions.status_code == 200
        assert len(versions.json()) == 1

        links = client.get(
            "/documents/links/by-target",
            params={"linked_type": "process", "linked_id": process_id},
        )
        assert links.status_code == 200
        assert len(links.json()) == 1


def test_document_can_link_to_process_step_and_task() -> None:
    with build_client() as client:
        process_response = client.post(
            "/processes",
            json={
                "company_id": "company-1",
                "name": "Linked Process",
                "status": "draft",
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
                "name": "Review document",
            },
        )
        assert step_response.status_code == 201
        step_id = step_response.json()["id"]

        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Document Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        task_response = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "process_step_id": step_id,
                "title": "Review document task",
            },
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        document_response = client.post(
            "/documents",
            json={
                "company_id": "company-1",
                "title": "Reference Manual",
                "document_type": "manual",
                "category": "operations",
            },
        )
        assert document_response.status_code == 201
        document_id = document_response.json()["id"]

        step_link = client.post(
            f"/documents/{document_id}/links",
            json={
                "company_id": "company-1",
                "document_id": document_id,
                "linked_type": "process_step",
                "linked_id": step_id,
                "relation_type": "manual",
            },
        )
        assert step_link.status_code == 201

        task_link = client.post(
            f"/documents/{document_id}/links",
            json={
                "company_id": "company-1",
                "document_id": document_id,
                "linked_type": "task",
                "linked_id": task_id,
                "relation_type": "reference",
            },
        )
        assert task_link.status_code == 201

        links = client.get(f"/documents/{document_id}/links")
        assert links.status_code == 200
        assert {link["linked_type"] for link in links.json()} == {"process_step", "task"}


def test_document_can_have_multiple_versions_and_current_version_updates() -> None:
    with build_client() as client:
        user_id = create_user(client)
        uploaded = client.post(
            "/documents/upload",
            data={
                "company_id": "company-1",
                "title": "Versioned Procedure",
                "document_type": "procedure",
                "change_summary": "Initial version",
            },
            files={"file": ("procedure-v1.txt", b"version one", "text/plain")},
        )
        assert uploaded.status_code == 201
        document_id = uploaded.json()["document"]["id"]
        first_version_id = uploaded.json()["version"]["id"]

        second_version = client.post(
            f"/documents/{document_id}/versions/upload",
            data={
                "company_id": "company-1",
                "created_by_user_id": user_id,
                "change_summary": "Updated procedure",
            },
            files={"file": ("procedure-v2.txt", b"version two", "text/plain")},
        )
        assert second_version.status_code == 201
        second_version_payload = second_version.json()
        assert second_version_payload["version_number"] == 2
        assert second_version_payload["file_name"] == "procedure-v2.txt"
        assert second_version_payload["change_summary"] == "Updated procedure"

        document = client.get(f"/documents/{document_id}")
        assert document.status_code == 200
        assert document.json()["current_version_id"] == second_version_payload["id"]
        assert document.json()["current_version_id"] != first_version_id

        versions = client.get(f"/documents/{document_id}/versions")
        assert versions.status_code == 200
        version_numbers = [version["version_number"] for version in versions.json()]
        assert version_numbers == [2, 1]


def test_document_link_rejects_unknown_target_type() -> None:
    with build_client() as client:
        document_response = client.post(
            "/documents",
            json={
                "company_id": "company-1",
                "title": "Reference Manual",
                "document_type": "manual",
            },
        )
        assert document_response.status_code == 201
        document_id = document_response.json()["id"]

        link = client.post(
            f"/documents/{document_id}/links",
            json={
                "company_id": "company-1",
                "document_id": document_id,
                "linked_type": "project",
                "linked_id": "project-1",
                "relation_type": "reference",
            },
        )
        assert link.status_code == 400
        assert link.json()["detail"]["message"] == "linked_type must be process, process_step, or task"


def test_document_rejects_missing_owner_reference() -> None:
    with build_client() as client:
        document_response = client.post(
            "/documents",
            json={
                "company_id": "company-1",
                "title": "Owned Manual",
                "document_type": "manual",
                "owner_user_id": "missing-user",
            },
        )
        assert document_response.status_code == 400
        assert document_response.json()["detail"]["message"] == (
            "owner_user_id does not reference an existing user"
        )
