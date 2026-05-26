from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_event(
    session: Session,
    *,
    business_id: int,
    entity_type: str,
    action: str,
    entity_id: int | None = None,
    payload: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        business_id=business_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload=payload or {},
    )
    session.add(log)
    return log
