"""
Módulo de Servicios para el Dominio de Autenticación.

Orquesta la lógica de negocio para la verificación de credenciales locales,
la validación de tokens de Google OAuth 2.0 y el aprovisionamiento de cuentas.
"""


from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidGoogleTokenError,
)
from app.core.config import settings
from app.core.security import verify_password
from app.users import service as user_service
from app.users.models import User


# ==============================================================================
# 1. UTILIDAD DE GOOGLE OAUTH
# ==============================================================================
def verify_google_token(token: str) -> dict | None:
    """
    Verifica la firma y validez de un ID Token emitido por Google.
    
    Returns:
        dict: Payload con la información del usuario si es válido.
        None: Si el token es inválido, expiró o no coincide el Client ID.
    """
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )


        return id_info
    
    except ValueError:





        return None


# ==============================================================================
# 2. SERVICIOS DE AUTENTICACIÓN
# ==============================================================================
async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    """
    Autentica un usuario con credenciales locales (email/password).

    Raises:
        InvalidCredentialsError: Si el usuario no existe, no tiene contraseña local
                                 o la clave no coincide.
        InactiveUserError: Si la cuenta está deshabilitada o suspendida.
    """

    user = await user_service.get_by_email(db, email=email)


    if not user or not user.hashed_password:
        raise InvalidCredentialsError()


    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InactiveUserError()


    return user



async def authenticate_google_user(
    db: AsyncSession, token: str
) -> User:
    """
    Valida un ID Token emitido por Google y obtiene o registra al usuario.

    Raises:
        InvalidGoogleTokenError: Si el token no es válido o faltan datos requeridos.
        InactiveUserError: Si el usuario existe pero su cuenta está inactiva.
    """

    id_info = verify_google_token(token)
    if not id_info:
        raise InvalidGoogleTokenError()

    google_id = id_info.get("sub")
    email = id_info.get("email")
    full_name = id_info.get("name")
    picture_url = id_info.get("picture")

    if not google_id or not email:
        raise InvalidGoogleTokenError("El token de Google no contiene la información requerida.")

    # 1. Buscar usuario previamente registrado con este Google ID
    user = await user_service.get_by_google_id(db, google_id=google_id)


    # 2. Si no existe, buscar por email para vincular la cuenta existente
    if not user:
        user = await user_service.get_by_email(db, email=email)
        if user:
            user.google_id = google_id
            if picture_url:
                user.picture_url = picture_url
            db.add(user)
            await db.commit()
            await db.refresh(user)

    # 3. Si sigue sin existir, crear un nuevo usuario con Google
    if not user:
        user = await user_service.create_google_user(
            db,
            email=email,
            full_name=full_name,
            google_id=google_id,
            picture_url=picture_url,
        )

    # 4. Validar estado de la cuenta
    if not user.is_active:
        raise InactiveUserError()

    return user