"""
Módulo de Routers HTTP para el Dominio de Usuarios.
"""

from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_db
from app.users import service as user_service
from app.users.dependencies import get_current_superuser, get_current_user
from app.users.models import User
from app.users.schemas import UserResponse, UserUpdate, UserUpdateAdmin

router = APIRouter(prefix="/users", tags=["Users"])


# --- 1. CONSULTAR MI PROPIO PERFIL ---
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil actual",
)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> Any:
    return current_user


# --- 2. ACTUALIZAR MI PROPIO PERFIL ---
@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil propio",
)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    updated_user = await user_service.update_user(
        db=db, user_id=current_user.id, user_in=user_in
    )
    return updated_user


# --- 3. LISTAR USUARIOS (ADMIN) ---
@router.get(
    "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios (Admin)",
)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await user_service.get_multi(db=db, skip=skip, limit=limit)


# --- 4. ACTUALIZAR USUARIO COMO ADMIN ---
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Modificar usuario por ID (Admin)",
)
async def admin_update_user(
    user_id: uuid.UUID,
    user_in: UserUpdateAdmin,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await user_service.update_user(db=db, user_id=user_id, user_in=user_in)