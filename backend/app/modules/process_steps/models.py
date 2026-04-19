import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    process_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("processes.id"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_role_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    responsible_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    instruction_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sla_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    process: Mapped["Process"] = relationship(back_populates="steps")
    instructions: Mapped[list["ProcessStepInstruction"]] = relationship(
        back_populates="process_step",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="process_step")


class ProcessStepInstruction(Base):
    __tablename__ = "process_step_instructions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    process_step_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("process_steps.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    process_step: Mapped["ProcessStep"] = relationship(back_populates="instructions")


from app.modules.tasks.models import Task
