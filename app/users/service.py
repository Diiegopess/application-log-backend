"""
Módulo de Servicio para el Dominio de Usuarios.

Encapsula todas las consultas asíncronas SQL a PostgreSQL utilizando SQLAlchemy 2.0.
Equivale a la capa de Servicios / Repositorios de datos.
"""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.users.models import User
from app.users.schemas import UserCreate, UserCreateGoogle, UserUpdate, UserUpdateAdmin


# --- 1. CONSULTAS DE LECTURA (READ) ---

async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Obtiene un usuario por su ID único de clave primaria."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Obtiene un usuario por su dirección de correo electrónico."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    """Obtiene un usuario por su ID único asignado por Google OAuth."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalars().first()


async def get_multi(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[User]:
    """
    Obtiene una lista paginada de usuarios.
    
    Args:
        skip: Cantidad de registros a omitir (OFFSET).
        limit: Cantidad máxima de registros a retornar (LIMIT).
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


# --- 2. OPERACIONES DE CREACIÓN (CREATE) ---

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Crea un nuevo usuario con credenciales locales (Email + Password).
    Aplica hashing con Bcrypt a la contraseña antes de persistir en BD.
    """
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        is_superuser=False,  # Por defecto ningún usuario registrado se crea como Admin
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_google_user(db: AsyncSession, user_in: UserCreateGoogle) -> User:
    """
    Crea un nuevo usuario proveniente del flujo de autenticación con Google.
    Establece hashed_password en None ya que su autenticación es delegada a Google.
    """
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        google_id=user_in.google_id,
        picture_url=user_in.picture_url,
        hashed_password=None,
        is_active=True,
        is_superuser=False,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# --- 3. OPERACIONES DE ACTUALIZACIÓN (UPDATE) ---

async def update_user(
    db: AsyncSession, db_user: User, user_in: UserUpdate | UserUpdateAdmin
) -> User:
    """
    Actualiza parcialmente un usuario existente en la base de datos.
    Soporta esquemas comunes (UserUpdate) y de administradores (UserUpdateAdmin).
    """
    # Extraemos solo los campos que el cliente envió explícitamente en el JSON
    update_data = user_in.model_dump(exclude_unset=True)

    # Si se envió una nueva contraseña en la actualización, se procesa su Hash
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        del update_data["password"]

    # Asignamos los demás atributos dinámicamente al objeto de SQLAlchemy
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user