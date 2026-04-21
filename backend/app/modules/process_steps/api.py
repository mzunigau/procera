from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_context import RequestContext, ensure_company_access, get_request_context
from app.modules.roles.permissions import Permission
from app.modules.process_steps.schemas import (
    ProcessStepCreate,
    ProcessStepInstructionCreate,
    ProcessStepInstructionRead,
    ProcessStepInstructionUpdate,
    ProcessStepRead,
    ProcessStepUpdate,
)
from app.modules.process_steps.service import ProcessStepService


router = APIRouter(tags=["process_steps"])


def get_process_step_service(db: Session = Depends(get_db)) -> ProcessStepService:
    return ProcessStepService(db)


@router.get("/process-steps", response_model=list[ProcessStepRead])
def list_process_steps(
    company_id: str | None = Query(default=None),
    process_id: str | None = Query(default=None),
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_VIEW)),
):
    return service.list_process_steps(company_id=context.company_id, process_id=process_id)


@router.post(
    "/processes/{process_id}/steps",
    response_model=ProcessStepRead,
    status_code=status.HTTP_201_CREATED,
)
def create_process_step(
    process_id: str,
    data: ProcessStepCreate,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    data.company_id = context.company_id
    data.process_id = process_id
    return service.create_process_step(data)


@router.get("/process-steps/{process_step_id}", response_model=ProcessStepRead)
def get_process_step(
    process_step_id: str,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_VIEW)),
):
    process_step = service.get_process_step(process_step_id)
    ensure_company_access(process_step, context)
    return process_step


@router.patch("/process-steps/{process_step_id}", response_model=ProcessStepRead)
def update_process_step(
    process_step_id: str,
    data: ProcessStepUpdate,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    ensure_company_access(service.get_process_step(process_step_id), context)
    return service.update_process_step(process_step_id, data)


@router.delete("/process-steps/{process_step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process_step(
    process_step_id: str,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    ensure_company_access(service.get_process_step(process_step_id), context)
    service.delete_process_step(process_step_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/process-step-instructions", response_model=list[ProcessStepInstructionRead])
def list_process_step_instructions(
    company_id: str | None = Query(default=None),
    process_step_id: str | None = Query(default=None),
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_VIEW)),
):
    return service.list_process_step_instructions(
        company_id=context.company_id,
        process_step_id=process_step_id,
    )


@router.post(
    "/process-steps/{process_step_id}/instructions",
    response_model=ProcessStepInstructionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_process_step_instruction(
    process_step_id: str,
    data: ProcessStepInstructionCreate,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    data.company_id = context.company_id
    data.process_step_id = process_step_id
    return service.create_process_step_instruction(data)


@router.get(
    "/process-step-instructions/{instruction_id}",
    response_model=ProcessStepInstructionRead,
)
def get_process_step_instruction(
    instruction_id: str,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_VIEW)),
):
    instruction = service.get_process_step_instruction(instruction_id)
    ensure_company_access(instruction, context)
    return instruction


@router.patch(
    "/process-step-instructions/{instruction_id}",
    response_model=ProcessStepInstructionRead,
)
def update_process_step_instruction(
    instruction_id: str,
    data: ProcessStepInstructionUpdate,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    ensure_company_access(service.get_process_step_instruction(instruction_id), context)
    return service.update_process_step_instruction(instruction_id, data)


@router.delete(
    "/process-step-instructions/{instruction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_process_step_instruction(
    instruction_id: str,
    service: ProcessStepService = Depends(get_process_step_service),
    context: RequestContext = Depends(require_permission(Permission.PROCESS_MANAGE)),
):
    ensure_company_access(service.get_process_step_instruction(instruction_id), context)
    service.delete_process_step_instruction(instruction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
