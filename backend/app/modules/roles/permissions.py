from enum import StrEnum


class Permission(StrEnum):
    AUDIT_VIEW = "audit:view"
    DOCUMENT_MANAGE = "document:manage"
    DOCUMENT_REVIEW = "document:review"
    DOCUMENT_VIEW = "document:view"
    PROCESS_MANAGE = "process:manage"
    PROCESS_PUBLISH = "process:publish"
    PROCESS_VIEW = "process:view"
    PROJECT_MANAGE = "project:manage"
    PROJECT_VIEW = "project:view"
    ROLE_MANAGE = "role:manage"
    TASK_MANAGE = "task:manage"
    TASK_REVIEW = "task:review"
    TASK_VIEW = "task:view"
    TEMPLATE_MANAGE = "template:manage"
    USER_MANAGE = "user:manage"


ALL_PERMISSIONS = {permission.value for permission in Permission}

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    "administrator": ALL_PERMISSIONS,
    "process owner": {
        Permission.PROCESS_MANAGE.value,
        Permission.PROCESS_PUBLISH.value,
        Permission.PROCESS_VIEW.value,
        Permission.DOCUMENT_VIEW.value,
        Permission.TASK_VIEW.value,
    },
    "project manager": {
        Permission.PROJECT_MANAGE.value,
        Permission.PROJECT_VIEW.value,
        Permission.TASK_MANAGE.value,
        Permission.TASK_VIEW.value,
        Permission.TEMPLATE_MANAGE.value,
    },
    "reviewer": {
        Permission.DOCUMENT_REVIEW.value,
        Permission.DOCUMENT_VIEW.value,
        Permission.TASK_REVIEW.value,
        Permission.TASK_VIEW.value,
    },
    "auditor": {
        Permission.AUDIT_VIEW.value,
        Permission.DOCUMENT_VIEW.value,
        Permission.PROCESS_VIEW.value,
        Permission.PROJECT_VIEW.value,
        Permission.TASK_VIEW.value,
    },
}


def permissions_for_role_names(role_names: list[str]) -> list[str]:
    permissions: set[str] = set()
    for role_name in role_names:
        permissions.update(ROLE_PERMISSION_MAP.get(role_name.strip().lower(), set()))
    return sorted(permissions)
