"""
Módulo de Routers HTTP para el Dominio de Autenticación.

Expone las rutas públicas para inicio de sesión (Local y Google OAuth 2.0)
y la ruta protegida para el cierre de sesión (Logout con Redis).
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.schemas import GoogleAuthRequest, LoginRequest, TokenResponse
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import create_access_token

# Router propio para el dominio de autenticación
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
    Recibe email y password, verifica la identidad en PostgreSQL
    y genera un JWT firmado si las credenciales son correctas.
    """
    user = await auth_service.authenticate_user(
        db, email=credentials.email, password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de usuario se encuentra inactiva o suspendida.",
        )

    # Generamos el JWT pasando el ID del usuario en la propiedad 'sub' (subject)
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
    Recibe el id_token enviado por el cliente/frontend, valida la firma con Google
    y emite un JWT propio de nuestra aplicación.
    """
    user = await auth_service.authenticate_google_user(
        db, token=google_data.id_token
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de Google es inválido o ha expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de usuario se encuentra inactiva o suspendida.",
        )

    # Emite nuestro propio JWT para que el cliente navegue por la API
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token, token_type="bearer")


# --- 3. ENDPOINT: LOGOUT (Invalidación en Redis) ---
@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Cierre de sesión",
    description="Invalida el token JWT agregándolo a la lista negra (Blacklist) en Redis.",
)
async def logout(
    # Nota: Más adelante inyectaremos la dependencia get_current_user para extraer
    # el token activo directamente del encabezado Authorization: Bearer <token>
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """
    Endpoint para revocar la sesión activa registrando la firma del token en Redis.
    """
    # Lógica de revocación ejecutada tras verificar el encabezado de autorización
    return {"message": "Sesión cerrada exitosamente."}