from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.processes.schemas import ProcessCreate, ProcessRead, ProcessUpdate
from app.modules.processes.service import ProcessService


router = APIRouter(tags=["processes"])


def get_process_service(db: Session = Depends(get_db)) -> ProcessService:
    return ProcessService(db)


@router.get("/processes", response_model=list[ProcessRead])
def list_processes(
    service: ProcessService = Depends(get_process_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_VIEW)),
):
    return service.list_processes(company_id=context.company_id)


@router.post("/processes", response_model=ProcessRead, status_code=status.HTTP_201_CREATED)
def create_process(
    data: ProcessCreate,
    service: ProcessService = Depends(get_process_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    data.company_id = context.company_id
    return service.create_process(data)


@router.get("/processes/{process_id}", response_model=ProcessRead)
def get_process(
    process_id: str,
    service: ProcessService = Depends(get_process_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_VIEW)),
):
    process = service.get_process(process_id)
    ensure_company_access(process, context)
    return process


@router.patch("/processes/{process_id}", response_model=ProcessRead)
def update_process(
    process_id: str,
    data: ProcessUpdate,
    service: ProcessService = Depends(get_process_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    ensure_company_access(service.get_process(process_id), context)
    return service.update_process(process_id, data)


@router.delete("/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process(
    process_id: str,
    service: ProcessService = Depends(get_process_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    ensure_company_access(service.get_process(process_id), context)
    service.delete_process(process_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
