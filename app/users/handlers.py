"""
Módulo de Controladores de Eventos (Event Handlers) del Dominio de Usuarios.

Escucha y procesa eventos de dominio emitidos por otros servicios (ej. Auth).
"""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.base import DomainEvent
from app.users import service as user_service
from app.users.exceptions import UserAlreadyExistsError
from app.users.schemas import UserProfileCreate

logger = logging.getLogger(__name__)


async def handle_user_registered_event(event: DomainEvent, db: AsyncSession) -> None:
    """
    Procesa el evento 'auth.user_registered' para crear automáticamente el
    perfil del usuario en la tabla 'users' de forma desacoplada e idempotente.
    """
    payload = event.payload
    user_id_str = payload.get("user_id")
    email = payload.get("email")

    if not user_id_str or not email:
        logger.error(f"[EVENT_HANDLER_ERROR] Evento {event.event_id} carece de user_id o email.")
        return

    # Construir el nombre completo a partir de los datos recibidos
    first_name = payload.get("first_name") or ""
    last_name = payload.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip() or None

    profile_in = UserProfileCreate(
        id=uuid.UUID(user_id_str),
        email=email,
        full_name=full_name,
        is_active=True,
        is_superuser=False,
    )

    try:
        await user_service.create_profile(db=db, profile_in=profile_in)
        logger.info(
            f"[PROFILE_CREATED] Perfil creado para usuario {email} (ID: {user_id_str}) mediante evento."
        )
    except UserAlreadyExistsError:
        # Idempotencia: Si el evento llega duplicado, no falla ni rompe el consumidor
        logger.warning(
            f"[PROFILE_EXISTS] El perfil para {email} ya existía previamente. Evento omitido."
        )
    except Exception as e:
        logger.error(
            f"[EVENT_PROCESSING_FAILED] Fallo al procesar creación de perfil: {str(e)}",
            exc_info=True,
        )
        raise e