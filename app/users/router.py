"""
Módulo de Endpoints HTTP para el Dominio de Usuarios.

Define las rutas para la administración y gestión CRUD de usuarios.
"""

from typing import Any, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users import service as user_service
from app.users.schemas import (
    UserCreate,
    UserResponse,
    UserUpdateAdmin,
)

# Router propio para el dominio de usuarios (Gestión/Administración)
router = APIRouter(prefix="/users", tags=["Users"])


# --- 1. ENDPOINT: REGISTRAR USUARIO (Administración) ---
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario local",
)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Recibe los datos de registro (email, password, full_name), verifica que el
    correo no exista y guarda el nuevo usuario.
    """
    existing_user = await user_service.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado.",
        )

    return await user_service.create_user(db, user_in=user_in)


# --- 2. ENDPOINT: LISTAR USUARIOS PAGINADOS ---
@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuarios paginados",
)
async def read_users(
    skip: int = Query(default=0, ge=0, description="Registros a omitir"),
    limit: int = Query(
        default=100, ge=1, le=100, description="Límite máximo de registros"
    ),
    db: AsyncSession = Depends(get_db),
) -> Sequence[Any]:
    """Retorna la lista de usuarios aplicando paginación (skip / limit)."""
    return await user_service.get_multi(db, skip=skip, limit=limit)


# --- 3. ENDPOINT: OBTENER USUARIO POR ID ---
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario por ID",
)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Busca y retorna un usuario por su clave primaria ID."""
    user = await user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario con ID {user_id} no existe.",
        )
    return user


# --- 4. ENDPOINT: ACTUALIZAR USUARIO POR ID ---
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario por ID",
)
async def update_user(
    user_id: int,
    user_in: UserUpdateAdmin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Actualiza parcialmente la información de un usuario."""
    db_user = await user_service.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario con ID {user_id} no existe.",
        )

    if user_in.email and user_in.email != db_user.email:
        existing_email = await user_service.get_by_email(db, email=user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo correo ya está en uso.",
            )

    return await user_service.update_user(db, db_user=db_user, user_in=user_in)