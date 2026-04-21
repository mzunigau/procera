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
from app.modules.audit.api import router as audit_router
from app.modules.process_steps.api import router as process_steps_router
from app.modules.processes.api import router as processes_router
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
    original_upload_storage_path = settings.upload_storage_path
    storage_directory = TemporaryDirectory()
    object.__setattr__(settings, "upload_storage_path", storage_directory.name)
    Base.metadata.create_all(bind=engine)
    app = FastAPI()
    app.include_router(processes_router)
    app.include_router(process_steps_router)
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


def test_task_crud() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Prepare operating instructions",
                "description": "Draft task guidance for the team.",
                "status": "pending",
                "priority": "medium",
                "requires_evidence": True,
                "requires_approval": False,
            },
        )
        assert created.status_code == 201
        task = created.json()
        assert task["project_id"] == project_id
        assert task["title"] == "Prepare operating instructions"

        task_id = task["id"]
        fetched = client.get(f"/tasks/{task_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == task_id

        updated = client.patch(
            f"/tasks/{task_id}",
            json={"status": "in_progress", "priority": "high"},
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "in_progress"
        assert updated.json()["priority"] == "high"

        reviewed = client.patch(f"/tasks/{task_id}", json={"status": "review"})
        assert reviewed.status_code == 200
        assert reviewed.json()["status"] == "review"

        listed = client.get("/tasks", params={"project_id": project_id})
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        deleted = client.delete(f"/tasks/{task_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/tasks/{task_id}")
        assert missing.status_code == 404


def test_task_create_requires_existing_project() -> None:
    with build_client() as client:
        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": "missing-project",
                "title": "Invalid task",
            },
        )
        assert created.status_code == 400
        assert created.json()["detail"]["message"] == "Project does not exist"


def test_task_creation_writes_audit_log() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Create audited task",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "task",
                "target_id": task_id,
                "action": "task.created",
            },
        )
        assert audit_logs.status_code == 200
        logs = audit_logs.json()
        assert len(logs) == 1
        assert logs[0]["summary"] == "Task created: Create audited task"
        assert logs[0]["before_data_json"] is None
        assert logs[0]["after_data_json"]["title"] == "Create audited task"


def test_task_status_change_writes_audit_log() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Change audited status",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        updated = client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
        assert updated.status_code == 200

        audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "task",
                "target_id": task_id,
                "action": "task.status_changed",
            },
        )
        assert audit_logs.status_code == 200
        logs = audit_logs.json()
        assert len(logs) == 1
        assert logs[0]["before_data_json"] == {"status": "pending"}
        assert logs[0]["after_data_json"] == {"status": "in_progress"}


def test_task_edit_writes_audit_log() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Edit audited task",
                "description": "Initial description",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        updated = client.patch(
            f"/tasks/{task_id}",
            json={
                "title": "Edited audited task",
                "description": "Updated description",
            },
        )
        assert updated.status_code == 200

        audit_logs = client.get(
            "/audit-logs",
            params={
                "target_type": "task",
                "target_id": task_id,
                "action": "task.updated",
            },
        )
        assert audit_logs.status_code == 200
        logs = audit_logs.json()
        assert len(logs) == 1
        assert logs[0]["before_data_json"]["title"] == "Edit audited task"
        assert logs[0]["after_data_json"]["title"] == "Edited audited task"
        assert logs[0]["before_data_json"]["description"] == "Initial description"
        assert logs[0]["after_data_json"]["description"] == "Updated description"


def test_task_attachment_reference_crud() -> None:
    with build_client() as client:
        user_id = create_user(client)
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
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
                "title": "Review reference attachment",
            },
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        created = client.post(
            f"/tasks/{task_id}/attachments",
            json={
                "company_id": "company-1",
                "file_name": "supplier-record.pdf",
                "storage_key": "external://documents/supplier-record.pdf",
                "content_type": "application/pdf",
                "size_bytes": 2048,
                "uploaded_by_user_id": user_id,
            },
        )
        assert created.status_code == 201
        attachment = created.json()
        assert attachment["task_id"] == task_id
        assert attachment["storage_key"] == "external://documents/supplier-record.pdf"

        attachment_id = attachment["id"]
        fetched = client.get(f"/tasks/attachments/{attachment_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == attachment_id

        listed = client.get(f"/tasks/{task_id}/attachments")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        updated = client.patch(
            f"/tasks/attachments/{attachment_id}",
            json={"file_name": "supplier-record-v2.pdf"},
        )
        assert updated.status_code == 200
        assert updated.json()["file_name"] == "supplier-record-v2.pdf"

        deleted = client.delete(f"/tasks/attachments/{attachment_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/tasks/attachments/{attachment_id}")
        assert missing.status_code == 404


def test_task_attachment_file_upload() -> None:
    with build_client() as client:
        user_id = create_user(client)
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
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
                "title": "Upload task attachment",
            },
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        uploaded = client.post(
            f"/tasks/{task_id}/attachments/upload",
            data={"company_id": "company-1", "uploaded_by_user_id": user_id},
            files={"file": ("note.txt", b"attachment content", "text/plain")},
        )
        assert uploaded.status_code == 201
        attachment = uploaded.json()
        assert attachment["task_id"] == task_id
        assert attachment["file_name"] == "note.txt"
        assert attachment["content_type"] == "text/plain"
        assert attachment["size_bytes"] == len(b"attachment content")
        assert attachment["uploaded_by_user_id"] == user_id


def test_task_comment_crud() -> None:
    with build_client() as client:
        user_id = create_user(client)
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
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
                "title": "Discuss task execution",
            },
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        created = client.post(
            f"/tasks/{task_id}/comments",
            json={
                "company_id": "company-1",
                "author_user_id": user_id,
                "body": "Please confirm the required evidence before completing this task.",
            },
        )
        assert created.status_code == 201
        comment = created.json()
        assert comment["task_id"] == task_id
        assert comment["author_user_id"] == user_id
        assert comment["body"] == "Please confirm the required evidence before completing this task."
        assert comment["created_at"] is not None
        assert comment["updated_at"] is not None

        comment_id = comment["id"]
        fetched = client.get(f"/tasks/comments/{comment_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == comment_id

        listed = client.get(f"/tasks/{task_id}/comments")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        updated = client.patch(
            f"/tasks/comments/{comment_id}",
            json={"body": "Evidence list confirmed."},
        )
        assert updated.status_code == 200
        assert updated.json()["body"] == "Evidence list confirmed."

        deleted = client.delete(f"/tasks/comments/{comment_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/tasks/comments/{comment_id}")
        assert missing.status_code == 404


def test_task_comment_requires_text() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
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
                "title": "Discuss task execution",
            },
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        created = client.post(
            f"/tasks/{task_id}/comments",
            json={
                "company_id": "company-1",
                "author_user_id": "user-1",
                "body": "",
            },
        )
        assert created.status_code == 422


def test_task_can_be_assigned_with_assigned_to() -> None:
    with build_client() as client:
        user_id = create_user(client)
        role_id = create_role(client)
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Assign responsible person",
                "assigned_to": {"type": "user", "id": user_id},
            },
        )
        assert created.status_code == 201
        task = created.json()
        assert task["assigned_to"] == {"type": "user", "id": user_id}
        assert task["assignee_user_id"] == user_id
        assert task["assignee_role_id"] is None

        task_id = task["id"]
        reassigned = client.patch(
            f"/tasks/{task_id}",
            json={"assigned_to": {"type": "role", "id": role_id}},
        )
        assert reassigned.status_code == 200
        reassigned_task = reassigned.json()
        assert reassigned_task["assigned_to"] == {"type": "role", "id": role_id}
        assert reassigned_task["assignee_user_id"] is None
        assert reassigned_task["assignee_role_id"] == role_id

        unassigned = client.patch(f"/tasks/{task_id}", json={"assigned_to": None})
        assert unassigned.status_code == 200
        unassigned_task = unassigned.json()
        assert unassigned_task["assigned_to"] is None
        assert unassigned_task["assignee_user_id"] is None
        assert unassigned_task["assignee_role_id"] is None


def test_task_assignment_rejects_mixed_assignment_styles() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Invalid assignment",
                "assigned_to": {"type": "user", "id": "user-1"},
                "assignee_role_id": "role-reviewer",
            },
        )
        assert created.status_code == 422


def test_task_assignment_rejects_missing_user_reference() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Assign missing person",
                "assigned_to": {"type": "user", "id": "missing-user"},
            },
        )
        assert created.status_code == 400
        assert created.json()["detail"]["message"] == (
            "assignee_user_id does not reference an existing user"
        )


def test_task_rejects_invalid_status_transition() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Complete setup",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        invalid = client.patch(f"/tasks/{task_id}", json={"status": "completed"})
        assert invalid.status_code == 400
        assert invalid.json()["detail"]["message"] == "Invalid task status transition"

        fetched = client.get(f"/tasks/{task_id}")
        assert fetched.status_code == 200
        assert fetched.json()["status"] == "pending"


def test_completed_task_status_is_terminal() -> None:
    with build_client() as client:
        project_response = client.post(
            "/projects",
            json={
                "company_id": "company-1",
                "name": "Operations Project",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        created = client.post(
            "/tasks",
            json={
                "company_id": "company-1",
                "project_id": project_id,
                "title": "Review and complete",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        assert client.patch(f"/tasks/{task_id}", json={"status": "in_progress"}).status_code == 200
        assert client.patch(f"/tasks/{task_id}", json={"status": "review"}).status_code == 200
        completed = client.patch(f"/tasks/{task_id}", json={"status": "completed"})
        assert completed.status_code == 200
        assert completed.json()["status"] == "completed"

        reopened = client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
        assert reopened.status_code == 400
        assert reopened.json()["detail"]["message"] == "Invalid task status transition"
