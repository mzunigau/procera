from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.process_steps.models import ProcessStep, ProcessStepInstruction
from app.modules.process_steps.schemas import (
    ProcessStepCreate,
    ProcessStepInstructionCreate,
    ProcessStepInstructionUpdate,
    ProcessStepUpdate,
)


class ProcessStepRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        process_id: str | None = None,
    ) -> list[ProcessStep]:
        query = select(ProcessStep).order_by(ProcessStep.step_order.asc())
        if company_id:
            query = query.where(ProcessStep.company_id == company_id)
        if process_id:
            query = query.where(ProcessStep.process_id == process_id)
        return list(self.db.scalars(query).all())

    def get(self, process_step_id: str) -> ProcessStep | None:
        return self.db.get(ProcessStep, process_step_id)

    def create(self, data: ProcessStepCreate, commit: bool = True) -> ProcessStep:
        process_step = ProcessStep(**data.model_dump())
        self.db.add(process_step)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(process_step)
        return process_step

    def update(self, process_step: ProcessStep, data: ProcessStepUpdate) -> ProcessStep:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(process_step, field, value)
        self.db.commit()
        self.db.refresh(process_step)
        return process_step

    def delete(self, process_step: ProcessStep) -> None:
        self.db.delete(process_step)
        self.db.commit()


class ProcessStepInstructionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        process_step_id: str | None = None,
    ) -> list[ProcessStepInstruction]:
        query = select(ProcessStepInstruction).order_by(ProcessStepInstruction.created_at.desc())
        if company_id:
            query = query.where(ProcessStepInstruction.company_id == company_id)
        if process_step_id:
            query = query.where(ProcessStepInstruction.process_step_id == process_step_id)
        return list(self.db.scalars(query).all())

    def get(self, instruction_id: str) -> ProcessStepInstruction | None:
        return self.db.get(ProcessStepInstruction, instruction_id)

    def create(self, data: ProcessStepInstructionCreate) -> ProcessStepInstruction:
        instruction = ProcessStepInstruction(**data.model_dump())
        self.db.add(instruction)
        self.db.commit()
        self.db.refresh(instruction)
        return instruction

    def update(
        self,
        instruction: ProcessStepInstruction,
        data: ProcessStepInstructionUpdate,
    ) -> ProcessStepInstruction:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instruction, field, value)
        self.db.commit()
        self.db.refresh(instruction)
        return instruction

    def delete(self, instruction: ProcessStepInstruction) -> None:
        self.db.delete(instruction)
        self.db.commit()
