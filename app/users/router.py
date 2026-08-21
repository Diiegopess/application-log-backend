"""
Módulo de Routers HTTP para el Dominio de Usuarios.
"""

from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.base import EventMetadata
from app.core.events.interfaces import IEventPublisher
from app.infrastructure.brokers.redis_producer import RedisStreamPublisher
from app.infrastructure.cache.redis_cache import get_redis_cache_client
from app.infrastructure.db.database import get_db
from app.users import service as user_service
from app.users.dependencies import get_current_superuser, get_current_user
from app.users.models import User
from app.users.schemas import (
    UserCreateAdmin,
    UserResponse,
    UserUpdate,
    UserUpdateAdmin,
)

router = APIRouter(prefix="/users", tags=["Users"])


def get_event_publisher() -> IEventPublisher:
    return RedisStreamPublisher(redis_client=get_redis_cache_client())


# --- 1. REGISTRAR USUARIO COMO ADMIN ---
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un usuario nuevo (Admin)",
)
async def admin_create_user(
    request: Request,
    user_in: UserCreateAdmin,
    current_admin: User = Depends(get_current_superuser),
    publisher: IEventPublisher = Depends(get_event_publisher),
    db: AsyncSession = Depends(get_db),
) -> Any:
    metadata = EventMetadata(
        user_id=str(current_admin.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return await user_service.admin_create_user(
        db=db,
        user_in=user_in,
        metadata=metadata,
        publisher=publisher,
    )


# --- 2. CONSULTAR MI PROPIO PERFIL ---
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


# --- 3. ACTUALIZAR MI PROPIO PERFIL ---
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
    return await user_service.update_user(
        db=db, user_id=current_user.id, user_in=user_in
    )


# --- 4. LISTAR USUARIOS (ADMIN) ---
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


# --- 5. ACTUALIZAR USUARIO COMO ADMIN ---
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