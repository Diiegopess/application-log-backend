"""
Manejadores de Eventos Asíncronos para el Dominio de Autenticación.
"""

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthCredential
from app.core.events.base import DomainEvent

logger = logging.getLogger(__name__)


async def handle_user_created_by_admin_event(
    event: DomainEvent, db: AsyncSession
) -> None:
    """
    Inserta la credencial de acceso cuando un usuario es creado administrativamente.
    """
    user_id_str = event.payload.get("user_id")
    email = event.payload.get("email")
    password_hash = event.payload.get("password_hash")
    is_active = event.payload.get("is_active", True)

    if not user_id_str or not email:
        logger.warning(
            f"[AUTH_HANDLER] Evento {event.event_id} omitido por falta de campos requeridos."
        )
        return

    user_id = uuid.UUID(user_id_str)

    # Verificar idempotencia
    stmt = select(AuthCredential).where(AuthCredential.id == user_id)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        logger.info(
            f"[AUTH_HANDLER] Credencial ya existente para user_id: {user_id}. Omitiendo."
        )
        return

    credential = AuthCredential(
        id=user_id,
        email=email,
        password_hash=password_hash,
        is_active=is_active,
        is_email_verified=True,
    )
    db.add(credential)
    await db.commit()
    logger.info(
        f"[AUTH_HANDLER] Credencial creada exitosamente para el usuario {email} (ID: {user_id})"
    )