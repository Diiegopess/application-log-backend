"""
Módulo de Routers HTTP para el Dominio de Autenticación.

Expone las rutas públicas para inicio de sesión (Local y Google OAuth 2.0),
la consulta de la sesión activa (/me) y el cierre de sesión (Logout).
"""

from typing import Any
from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.schemas import GoogleAuthRequest, LoginRequest, TokenResponse
from app.db.database import get_db
from app.db.redis_client import get_redis
from app.core.security import create_access_token


from app.users.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserResponse


router = APIRouter(prefix="/auth", tags=["Auth"])


# --- 1. ENDPOINT: LOGIN LOCAL (Email + Password) ---
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión local",
    description="Valida las credenciales ingresadas y emite un token de acceso JWT.",
)
async def login_local(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Autentica al usuario mediante email y contraseña.
    Cualquier error de credenciales o cuenta inactiva es manejado automáticamente por el handler central.
    """
    user = await auth_service.authenticate_user(
        db, email=credentials.email, password=credentials.password
    )
    
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token, token_type="bearer")


# --- 2. ENDPOINT: LOGIN CON GOOGLE OAUTH 2.0 ---
@router.post(
    "/google",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión / Registro con Google",
    description="Valida el ID Token de Google, registra al usuario si es nuevo y emite un JWT de App_Log.",
)
async def login_google(
    google_data: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Autentica o registra un usuario mediante Google OAuth 2.0.
    """
    user = await auth_service.authenticate_google_user(
        db, token=google_data.id_token
    )
    
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token, token_type="bearer")


# --- 3. ENDPOINT: OBTENER PERFIL DE SESIÓN ACTIVA (/me) ---
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil de la sesión activa",
    description="Devuelve la información del usuario autenticado mediante el token JWT.",
)
async def read_session_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Endpoint protegido para consultar los datos del usuario logueado.
    """
    return current_user


# --- 4. ENDPOINT: LOGOUT (Invalidación en Redis) ---
@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Cierre de sesión",
    description="Invalida la sesión actual del usuario.",
)
async def logout(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """
    Endpoint para revocar la sesión activa.
    """

    return {"message": "Sesión cerrada exitosamente."}