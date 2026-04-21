from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine
from app.modules.audit.api import router as audit_router
from app.modules.documents.api import router as documents_router
from app.modules.process_steps.api import router as process_steps_router
from app.modules.processes.api import router as processes_router
from app.modules.projects.api import (
    project_process_instances_router,
    router as projects_router,
)
from app.modules.roles.api import router as roles_router
from app.modules.tasks.api import router as tasks_router
from app.modules.templates.api import router as templates_router
from app.modules.users.api import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Procera API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(projects_router)
app.include_router(project_process_instances_router)
app.include_router(tasks_router)
app.include_router(processes_router)
app.include_router(process_steps_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(audit_router)
app.include_router(documents_router)
app.include_router(templates_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
