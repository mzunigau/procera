from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.process_steps.models import ProcessStep, ProcessStepInstruction
from app.modules.process_steps.repository import (
    ProcessStepInstructionRepository,
    ProcessStepRepository,
)
from app.modules.process_steps.schemas import (
    ProcessStepCreate,
    ProcessStepInstructionCreate,
    ProcessStepInstructionUpdate,
    ProcessStepUpdate,
)
from app.modules.processes.repository import ProcessRepository


class ProcessStepService:
    def __init__(self, db: Session) -> None:
        self.processes = ProcessRepository(db)
        self.steps = ProcessStepRepository(db)
        self.instructions = ProcessStepInstructionRepository(db)

    def list_process_steps(
        self,
        company_id: str | None = None,
        process_id: str | None = None,
    ) -> list[ProcessStep]:
        return self.steps.list(company_id=company_id, process_id=process_id)

    def get_process_step(self, process_step_id: str) -> ProcessStep:
        process_step = self.steps.get(process_step_id)
        if process_step is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Process step not found"},
            )
        return process_step

    def create_process_step(self, data: ProcessStepCreate) -> ProcessStep:
        self._ensure_process_matches_company(data.process_id, data.company_id)
        return self.steps.create(data)

    def update_process_step(self, process_step_id: str, data: ProcessStepUpdate) -> ProcessStep:
        process_step = self.get_process_step(process_step_id)
        if data.process_id is not None:
            self._ensure_process_matches_company(data.process_id, process_step.company_id)
        return self.steps.update(process_step, data)

    def delete_process_step(self, process_step_id: str) -> None:
        process_step = self.get_process_step(process_step_id)
        self.steps.delete(process_step)

    def list_process_step_instructions(
        self,
        company_id: str | None = None,
        process_step_id: str | None = None,
    ) -> list[ProcessStepInstruction]:
        return self.instructions.list(
            company_id=company_id,
            process_step_id=process_step_id,
        )

    def get_process_step_instruction(self, instruction_id: str) -> ProcessStepInstruction:
        instruction = self.instructions.get(instruction_id)
        if instruction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Process step instruction not found"},
            )
        return instruction

    def create_process_step_instruction(
        self,
        data: ProcessStepInstructionCreate,
    ) -> ProcessStepInstruction:
        self._ensure_process_step_matches_company(data.process_step_id, data.company_id)
        return self.instructions.create(data)

    def update_process_step_instruction(
        self,
        instruction_id: str,
        data: ProcessStepInstructionUpdate,
    ) -> ProcessStepInstruction:
        instruction = self.get_process_step_instruction(instruction_id)
        if data.process_step_id is not None:
            self._ensure_process_step_matches_company(
                data.process_step_id,
                instruction.company_id,
            )
        return self.instructions.update(instruction, data)

    def delete_process_step_instruction(self, instruction_id: str) -> None:
        instruction = self.get_process_step_instruction(instruction_id)
        self.instructions.delete(instruction)

    def _ensure_process_matches_company(self, process_id: str, company_id: str) -> None:
        process = self.processes.get(process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process does not exist"},
            )
        if process.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process belongs to a different company"},
            )

    def _ensure_process_step_matches_company(self, process_step_id: str, company_id: str) -> None:
        process_step = self.steps.get(process_step_id)
        if process_step is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process step does not exist"},
            )
        if process_step.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Process step belongs to a different company"},
            )
