"""Audit service — write structured audit log entries."""
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_event(
    session: Session,
    *,
    entity_type: str,
    entity_id: int | None,
    action: str,
    business_id: int | None = None,
    actor: str | None = None,
    payload: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        business_id=business_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        payload=payload,
    )
    session.add(entry)
    return entry
