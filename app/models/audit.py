from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    def __str__(self) -> str:
        return f"{self.entity_type} #{self.entity_id} – {self.action}"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True
    )
    entity_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    actor: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    payload: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )
