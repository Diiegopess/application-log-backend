"""
Módulo de Servicios para el Dominio de Autenticación.

Contiene la lógica de negocio pura encargada de:
1. Validar el token JWT de Google (vía Google OAuth 2.0).
2. Autenticar usuarios con credenciales locales (email/password).
3. Registrar o vincular automáticamente usuarios que inician sesión con Google.
"""

from typing import Optional
from google.auth.exceptions import TransportError
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.users import service as user_service
from app.users.models import User


# ==============================================================================
# 1. VERIFICACIÓN CRIPTOGRÁFICA DEL TOKEN DE GOOGLE
# ==============================================================================
def verify_google_token(token: str) -> Optional[dict]:
    """
    Valida un id_token emitido por Google OAuth 2.0.

    ¿Cómo funciona?
    1. Descarga las claves públicas oficiales de Google (o las lee de caché).
    2. Comprueba matemáticamente la firma digital del token.
    3. Verifica que el token no esté vencido (exp) y que haya sido emitido
       específicamente para nuestro GOOGLE_CLIENT_ID (aud).

    Args:
        token (str): El id_token que nos envió el Frontend en React.

    Returns:
        Optional[dict]: Un diccionario con el perfil del usuario (email, sub, name, etc.)
                        o None si el token es inválido, expiró o falló la conexión.
    """
    try:
        # requests.Request() es el cliente HTTP interno que usa la librería de Google
        # para conectarse a https://www.googleapis.com/oauth2/v3/certs si necesita descargar claves.
        id_info = google_id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        # Si todo es correcto, id_info es un diccionario con la payload del JWT
        return id_info

    except ValueError:
        # Se dispara si el token fue manipulado, está mal formateado o expiró
        return None

    except TransportError:
        # Se dispara si el contenedor de Docker pierde conexión a internet o fallan los DNS
        # al intentar descargar las claves públicas de Google. Evita un error 500 en el servidor.
        return None


# ==============================================================================
# 2. AUTENTICACIÓN LOCAL (EMAIL + CONTRASEÑA)
# ==============================================================================
async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """
    Autentica un usuario registrado mediante el formulario tradicional.

    Args:
        db (AsyncSession): Sesión asíncrona de base de datos PostgreSQL.
        email (str): Correo ingresado por el usuario.
        password (str): Contraseña en texto plano ingresada en el formulario.

    Returns:
        Optional[User]: La entidad User si las credenciales son válidas, o None si no.
    """
    # 1. Busca el usuario en la BD por su correo electrónico
    user = await user_service.get_by_email(db, email=email)
    if not user:
        return None  # El usuario no existe

    # 2. Si el usuario se registró con Google y NO tiene contraseña local
    if not user.hashed_password:
        return None

    # 3. Compara el hash almacenado en PostgreSQL con la contraseña ingresada usando Bcrypt
    if not verify_password(password, user.hashed_password):
        return None  # Contraseña incorrecta

    # 4. Credenciales correctas, se retorna el objeto del usuario
    return user


# ==============================================================================
# 3. AUTENTICACIÓN Y AUTORREGISTRO CON GOOGLE OAUTH
# ==============================================================================
async def authenticate_google_user(
    db: AsyncSession, token: str
) -> Optional[User]:
    """
    Orquesta el flujo completo de inicio de sesión o registro automático con Google.

    Pasos del flujo:
    1. Verifica la firma del id_token enviada por React.
    2. Busca si el usuario ya existe en PostgreSQL mediante su 'google_id' o 'email'.
    3. Si es un usuario completamente nuevo, lo crea automáticamente en la base de datos.
    4. Si ya existía por email local pero no tenía google_id, le vincula su cuenta de Google.

    Args:
        db (AsyncSession): Sesión de base de datos.
        token (str): El id_token de Google.

    Returns:
        Optional[User]: La instancia del usuario listo para generar su JWT propio, o None.
    """
    # Paso A: Validar la firma criptográfica con Google
    id_info = verify_google_token(token)
    if not id_info:
        return None  # Token inválido o corrupto

    # Paso B: Extraer datos del perfil validado por Google
    google_id = id_info.get("sub")        # Identificador único e inmutable de Google
    email = id_info.get("email")          # Correo del usuario
    full_name = id_info.get("name")      # Nombre completo
    picture_url = id_info.get("picture")  # URL del avatar/foto de perfil

    if not google_id or not email:
        return None  # Faltan datos esenciales en el token

    # Paso C: Buscar si el usuario ya se ha autenticado con Google anteriormente
    user = await user_service.get_by_google_id(db, google_id=google_id)
    if user:
        return user  # Usuario recurrente de Google, listo

    # Paso D: Si no se encontró por google_id, buscar si existe una cuenta previa con ese mismo email
    user = await user_service.get_by_email(db, email=email)

    if user:
        # El usuario se había registrado con contraseña en el pasado.
        # Ahora vinculamos su google_id y actualizamos su foto de perfil.
        user.google_id = google_id
        if picture_url:
            user.picture_url = picture_url
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # Paso E: Si el correo tampoco existe, es un USUARIO NUEVO. Lo registramos en PostgreSQL.
    new_user = await user_service.create_google_user(
        db,
        email=email,
        full_name=full_name,
        google_id=google_id,
        picture_url=picture_url,
    )
    return new_user