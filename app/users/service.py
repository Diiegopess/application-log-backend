"""
Módulo de Servicios para el Dominio de Usuarios.

Contiene las operaciones de base de datos y reglas de negocio para usuarios.
"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.users.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdateAdmin

async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Busca un usuario por su ID primario."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_by_id_or_fail(db: AsyncSession, user_id: int) -> User:
    """
    Busca un usuario por ID. Si no existe, lanza UserNotFoundError automáticamente.
    """
    user = await get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(user_id=user_id)
    return user


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Busca un usuario por su correo electrónico."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    """Busca un usuario por su identificador único de Google."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalars().first()


async def get_multi(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[User]:
    """Retorna una lista paginada de usuarios."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()




async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Crea un usuario con credenciales locales tras verificar unicidad de email.
    """
    existing_user = await get_by_email(db, email=user_in.email)
    if existing_user:
        raise EmailAlreadyExistsError(email=user_in.email)

    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_google_user(
    db: AsyncSession,
    email: str,
    full_name: str | None,
    google_id: str,
    picture_url: str | None,
) -> User:
    """Registra automáticamente a un usuario autenticado por primera vez vía Google."""
    db_user = User(
        email=email,
        full_name=full_name,
        google_id=google_id,
        picture_url=picture_url,
        hashed_password=None,
        is_active=True,
        is_superuser=False,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user




async def update_user(
    db: AsyncSession, user_id: int, user_in: UserUpdateAdmin
) -> User:
    """
    Actualiza la información de un usuario validando existencia y correo único.
    """
    # 1. Asegura que el usuario exista
    db_user = await get_by_id_or_fail(db, user_id)

    # 2. Si cambia de email, verifica que el nuevo no esté tomado
    if user_in.email and user_in.email != db_user.email:
        existing_email = await get_by_email(db, email=user_in.email)
        if existing_email:
            raise EmailAlreadyExistsError(email=user_in.email)

    # 3. Aplica los cambios enviados
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))



    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user