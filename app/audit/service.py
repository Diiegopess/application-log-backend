"""
Módulo de Servicios para el Dominio de Auditoría.
"""

from datetime import datetime
from typing import Sequence
import uuid
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.schemas import AuditLogCreate


async def record_audit_log(db: AsyncSession, log_in: AuditLogCreate) -> AuditLog:
    """
    Inserta un nuevo registro de auditoría de forma inmutable.
    """
    db_log = AuditLog(
        event_id=log_in.event_id,
        event_type=log_in.event_type,
        user_id=log_in.user_id,
        ip_address=log_in.ip_address,
        user_agent=log_in.user_agent,
        correlation_id=log_in.correlation_id,
        payload=log_in.payload,
        occurred_at=log_in.occurred_at,
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    event_type: str | None = None,
    user_id: uuid.UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> Sequence[AuditLog]:
    """
    Obtiene el historial de auditoría con filtros opcionales ordenado descendentemente.
    """
    stmt = select(AuditLog)

    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if from_date:
        stmt = stmt.where(AuditLog.occurred_at >= from_date)
    if to_date:
        stmt = stmt.where(AuditLog.occurred_at <= to_date)

    stmt = stmt.order_by(desc(AuditLog.occurred_at)).offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()