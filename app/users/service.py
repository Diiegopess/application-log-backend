"""
Módulo de Servicios para el Dominio de Usuarios.

Contiene las operaciones de base de datos y reglas de negocio
exclusivas para perfiles de usuario (tabla 'users').
"""

import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.users.models import User
from app.users.schemas import UserProfileCreate, UserUpdate, UserUpdateAdmin


# ==============================================================================
# 1. CONSULTAS DE LECTURA
# ==============================================================================

async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Busca un usuario por su UUID primario."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_by_id_or_fail(db: AsyncSession, user_id: uuid.UUID) -> User:
    """
    Busca un usuario por UUID. Si no existe, lanza UserNotFoundError.
    """
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
    """
    Crea un perfil de usuario asignándole el UUID previamente emitido por Auth.
    """
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


# ==============================================================================
# 3. ACTUALIZACIÓN DE PERFILES
# ==============================================================================

async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_in: UserUpdate | UserUpdateAdmin,
) -> User:
    """
    Actualiza los datos del perfil de un usuario validando existencia y unicidad de email.
    """
    db_user = await get_by_id_or_fail(db, user_id)

    # Si se intenta cambiar de email, verificar que no esté ocupado
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