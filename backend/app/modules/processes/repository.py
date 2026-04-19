from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.processes.models import Process
from app.modules.processes.schemas import ProcessCreate, ProcessUpdate


class ProcessRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, company_id: str | None = None) -> list[Process]:
        query = select(Process).order_by(Process.created_at.desc())
        if company_id:
            query = query.where(Process.company_id == company_id)
        return list(self.db.scalars(query).all())

    def get(self, process_id: str) -> Process | None:
        return self.db.get(Process, process_id)

    def create(self, data: ProcessCreate) -> Process:
        process = Process(**data.model_dump())
        self.db.add(process)
        self.db.commit()
        self.db.refresh(process)
        return process

    def update(self, process: Process, data: ProcessUpdate) -> Process:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(process, field, value)
        self.db.commit()
        self.db.refresh(process)
        return process

    def delete(self, process: Process) -> None:
        self.db.delete(process)
        self.db.commit()
