"""
Módulo de Servicios para el Dominio de Usuarios.

Contiene las operaciones de base de datos y reglas de negocio
exclusivas para perfiles de usuario (tabla 'users').
"""

import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events.base import DomainEvent, EventMetadata
from app.core.events.interfaces import IEventPublisher
from app.core.security import hash_password
from app.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.users.models import User
from app.users.schemas import (
    UserCreateAdmin,
    UserProfileCreate,
    UserUpdate,
    UserUpdateAdmin,
)


# ==============================================================================
# 1. CONSULTAS DE LECTURA
# ==============================================================================

async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Busca un usuario por su UUID primario."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_by_id_or_fail(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Busca un usuario por UUID. Si no existe, lanza UserNotFoundError."""
    user = await get_by_id(db, user_id=user_id)
    if not user:
        raise UserNotFoundError()
    return user


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Busca un usuario por su correo electrónico."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_multi(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[User]:
    """Retorna una lista paginada de usuarios."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


# ==============================================================================
# 2. CREACIÓN Y APROVISIONAMIENTO DE PERFILES
# ==============================================================================

async def create_profile(db: AsyncSession, profile_in: UserProfileCreate) -> User:
    """Crea un perfil de usuario asignándole el UUID recibido desde Auth."""
    existing_user = await get_by_email(db, email=profile_in.email)
    if existing_user:
        raise UserAlreadyExistsError()

    db_user = User(
        id=profile_in.id,
        email=profile_in.email,
        full_name=profile_in.full_name,
        is_active=profile_in.is_active,
        is_superuser=profile_in.is_superuser,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def admin_create_user(
    db: AsyncSession,
    user_in: UserCreateAdmin,
    metadata: EventMetadata,
    publisher: IEventPublisher,
) -> User:
    """
    Crea el usuario administrativamente y publica el evento para que Auth provisione las credenciales.
    """
    existing_user = await get_by_email(db, email=user_in.email)
    if existing_user:
        raise UserAlreadyExistsError()

    user_id = uuid.uuid4()

    # Construir nombre completo a partir de nombres y apellidos
    names = [n for n in [user_in.first_name, user_in.last_name] if n]
    full_name = " ".join(names) if names else None

    # 1. Crear el usuario en la tabla 'users'
    db_user = User(
        id=user_id,
        email=user_in.email,
        full_name=full_name,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # 2. Publicar evento a Redis Streams para sincronizar Auth y registrar Auditoría
    event = DomainEvent(
        event_type="user.created_by_admin",
        metadata=metadata,
        payload={
            "user_id": str(db_user.id),
            "email": db_user.email,
            "password_hash": hash_password(user_in.password),
            "is_active": db_user.is_active,
        },
    )
    await publisher.publish(stream_or_topic=settings.AUTH_STREAM_NAME, event=event)

    return db_user


# ==============================================================================
# 3. ACTUALIZACIÓN DE PERFILES
# ==============================================================================

async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_in: UserUpdate | UserUpdateAdmin,
) -> User:
    """Actualiza los datos del perfil de un usuario validando unicidad de email."""
    db_user = await get_by_id_or_fail(db, user_id)

    if user_in.email and user_in.email != db_user.email:
        existing_email = await get_by_email(db, email=user_in.email)
        if existing_email:
            raise UserAlreadyExistsError()

    update_data = user_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user