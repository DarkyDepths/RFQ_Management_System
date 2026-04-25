"""
Workflow datasource — database queries for the `workflow` table.

Methods:
- list()                     — SELECT all workflows (active and inactive)
- get_by_id(workflow_id)     — SELECT single workflow with embedded stage templates
- update(workflow_id, data)  — partial UPDATE (name, description, is_active, is_default)
"""

from __future__ import annotations


from sqlalchemy.orm import Session

from src.models.workflow import Workflow


class WorkflowDatasource:

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, workflow_id) -> Workflow | None:
        """Fetch workflow with its stage templates (auto-loaded via relationship)."""
        return self.session.query(Workflow).filter(Workflow.id == workflow_id).first()

    def list_all(self) -> list[Workflow]:
        """Return all workflows (active and inactive)."""
        return self.session.query(Workflow).order_by(Workflow.name).all()

    def clear_default(self):
        """Unset is_default on all workflows. Called before setting a new default."""
        self.session.query(Workflow).filter(Workflow.is_default == True).update(  # noqa: E712
            {"is_default": False}
        )
        self.session.flush()

    def update(self, workflow: Workflow, data: dict) -> Workflow:
        """Partial update."""
        for key, value in data.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        self.session.flush()
        self.session.refresh(workflow)
        return workflow
