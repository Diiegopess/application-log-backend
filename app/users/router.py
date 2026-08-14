"""
Módulo de Endpoints HTTP para el Dominio de Usuarios.

Define las rutas para la administración y gestión CRUD de usuarios.
"""
from typing import Sequence
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

from app.users import service as user_service
from app.users.models import User
from app.users.schemas import (
    UserCreate,
    UserResponse,
    UserUpdateAdmin,
)


router = APIRouter(prefix="/users", tags=["Users"])


# --- 1. ENDPOINT: REGISTRAR USUARIO (Administración) ---
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario local",
    description="Crea un nuevo usuario en la base de datos tras verificar la unicidad del correo.",
)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Recibe los datos del usuario y delega la creación al servicio de negocio.
    """
    return await user_service.create_user(db, user_in=user_in)


# --- 2. ENDPOINT: LISTAR USUARIOS PAGINADOS ---
@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuarios paginados",
    description="Retorna una colección de usuarios aplicando paginación por desplazamiento (skip/limit).",
)
async def read_users(
    skip: int = Query(default=0, ge=0, description="Registros a omitir"),
    limit: int = Query(
        default=100, ge=1, le=100, description="Límite máximo de registros"
    ),
    db: AsyncSession = Depends(get_db),
) -> Sequence[User]:
    """
    Consulta la lista paginada de usuarios registrados.
    """
    return await user_service.get_multi(db, skip=skip, limit=limit)


# --- 3. ENDPOINT: OBTENER USUARIO POR ID ---
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario por ID",
    description="Busca y retorna la ficha completa de un usuario por su clave primaria.",
)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Recupera el perfil de un usuario específico. Lanza 404 si no existe.
    """
    return await user_service.get_by_id_or_fail(db, user_id=user_id)


# --- 4. ENDPOINT: ACTUALIZAR USUARIO POR ID ---
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario por ID",
    description="Actualiza campos específicos de un usuario existente.",
)
async def update_user(
    user_id: int,
    user_in: UserUpdateAdmin,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Modifica la información de un usuario validando disponibilidad del correo.
    """
    return await user_service.update_user(db, user_id=user_id, user_in=user_in)