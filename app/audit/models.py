"""
Módulo de Modelos SQLAlchemy para el Dominio de Auditoría.

Define la estructura de 'audit_logs' para registro inmutable de eventos.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    # Identificador único del registro de auditoría
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Identificador original del evento de dominio
    event_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # Tipo de evento (ej. 'auth.user_registered', 'auth.login_success')
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Sujeto / Usuario involucrado (si aplica)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=True,
    )

    # Metadatos de red y contexto de ejecución
    ip_address: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(512), default="unknown", nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    # Carga útil completa del evento en formato JSON estructurado
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamp de ocurrencia real del evento
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Timestamp de registro físico en la base de datos
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )