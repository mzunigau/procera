from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.templates.models import Template, TemplateType
from app.modules.templates.schemas import TemplateCreate, TemplateUpdate


class TemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        company_id: str | None = None,
        template_type: TemplateType | None = None,
    ) -> list[Template]:
        query = select(Template).order_by(Template.created_at.desc())
        if company_id:
            query = query.where(Template.company_id == company_id)
        if template_type:
            query = query.where(Template.template_type == template_type)
        return list(self.db.scalars(query).all())

    def get(self, template_id: str) -> Template | None:
        return self.db.get(Template, template_id)

    def create(self, data: TemplateCreate) -> Template:
        template = Template(**data.model_dump())
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update(self, template: Template, data: TemplateUpdate) -> Template:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template: Template) -> None:
        self.db.delete(template)
        self.db.commit()
