from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.reference_validation import ReferenceValidator
from app.modules.processes.models import Process
from app.modules.processes.repository import ProcessRepository
from app.modules.processes.schemas import ProcessCreate, ProcessUpdate


class ProcessService:
    def __init__(self, db: Session) -> None:
        self.processes = ProcessRepository(db)
        self.reference_validator = ReferenceValidator(db)

    def list_processes(self, company_id: str | None = None) -> list[Process]:
        return self.processes.list(company_id=company_id)

    def get_process(self, process_id: str) -> Process:
        process = self.processes.get(process_id)
        if process is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Process not found"},
            )
        return process

    def create_process(self, data: ProcessCreate) -> Process:
        self.reference_validator.ensure_user_matches_company(
            data.owner_user_id,
            data.company_id,
            "owner_user_id",
        )
        return self.processes.create(data)

    def update_process(self, process_id: str, data: ProcessUpdate) -> Process:
        process = self.get_process(process_id)
        if "owner_user_id" in data.model_fields_set:
            self.reference_validator.ensure_user_matches_company(
                data.owner_user_id,
                process.company_id,
                "owner_user_id",
            )
        return self.processes.update(process, data)

    def delete_process(self, process_id: str) -> None:
        process = self.get_process(process_id)
        self.processes.delete(process)
