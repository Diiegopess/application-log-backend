"""
Módulo de Servicio para el Dominio de Autenticación.

Coordina la verificación de credenciales locales, validación de ID Tokens de Google,
creación automática de usuarios (Provisionamiento) y gestión de revocación
de tokens JWT mediante una lista negra (Blacklist) en Redis.
"""

from datetime import datetime, timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.users import service as user_service
from app.users.models import User
from app.users.schemas import UserCreateGoogle


# --- 1. VERIFICACIÓN Y AUTENTICACIÓN LOCAL ---

async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User | None:
    """
    Autentica un usuario comparando su email y contraseña en texto plano.

    Flujo de Negocio:
    1. Busca el usuario en PostgreSQL por su correo.
    2. Si no existe o no tiene contraseña (ej. se registró vía Google), rechaza.
    3. Compara la contraseña ingresada contra el hash Bcrypt de la base de datos.
    """
    user = await user_service.get_by_email(db, email=email)
    if not user:
        return None

    # Si se registró únicamente vía Google, hashed_password será None en la BD
    if not user.hashed_password:
        return None

    # Verificación segura con Bcrypt
    if not verify_password(password, user.hashed_password):
        return None

    return user


# --- 2. VERIFICACIÓN Y PROVISIONAMIENTO VÍA GOOGLE OAUTH 2.0 ---

async def authenticate_google_user(db: AsyncSession, token: str) -> User | None:
    """
    Verifica un ID Token emitido por Google y obtiene o crea al usuario en PostgreSQL.

    Flujo de Negocio (Provisionamiento Automático):
    1. Contacta/valida criptográficamente el token con la librería oficial de Google.
    2. Extrae 'sub' (google_id), 'email', 'name' y 'picture'.
    3. Si el usuario existe por google_id, lo retorna.
    4. Si existe por email pero sin google_id, vincula los datos de Google a su cuenta.
    5. Si no existe en la base de datos, lo crea automáticamente.
    """
    try:
        # Objeto de transporte HTTP requerido por la librería de Google
        request = google_requests.Request()

        # Valida que el token sea auténtico y pertenezca a nuestro GOOGLE_CLIENT_ID
        id_info = google_id_token.verify_oauth2_token(
            token, request, settings.GOOGLE_CLIENT_ID
        )

        # Datos del perfil entregados por Google (Claims)
        google_id: str = id_info["sub"]
        email: str = id_info["email"]
        full_name: str | None = id_info.get("name")
        picture_url: str | None = id_info.get("picture")

        # Caso A: Buscar por ID único de Google
        user = await user_service.get_by_google_id(db, google_id=google_id)
        if user:
            return user

        # Caso B: Buscar por correo electrónico
        user = await user_service.get_by_email(db, email=email)
        if user:
            # Vinculamos el google_id y foto al usuario local preexistente
            user.google_id = google_id
            if picture_url and not user.picture_url:
                user.picture_url = picture_url
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

        # Caso C: Usuario totalmente nuevo (Registro Automático)
        user_in = UserCreateGoogle(
            email=email,
            full_name=full_name,
            google_id=google_id,
            picture_url=picture_url,
        )
        new_user = await user_service.create_google_user(db, user_in=user_in)
        return new_user

    except ValueError:
        # Si el token caducó, la firma fue alterada o no coincide con GOOGLE_CLIENT_ID
        return None


# --- 3. GESTIÓN DE REVOCACIÓN DE TOKENS (LOGOUT EN REDIS) ---

async def blacklist_token(redis: Redis, token: str, payload: dict) -> None:
    """
    Agrega la firma de un JWT a la lista negra en Redis durante el cierre de sesión.

    Cálculo Inteligente de Expiración (TTL):
    En lugar de almacenar el token indefinidamente en la memoria de Redis,
    calculamos cuántos segundos le quedan de validez según el claim 'exp'.
    Seteamos ese TTL en Redis; una vez transcurrido ese tiempo, el JWT habrá
    expirado por sí solo y Redis liberará la memoria automáticamente.
    """
    exp_timestamp = payload.get("exp")
    if not exp_timestamp:
        return

    # Tiempo actual en timestamp UNIX (Segundos en UTC)
    now_timestamp = datetime.now(timezone.utc).timestamp()
    
    # Tiempo remanente de vida útil del token en segundos
    ttl_seconds = int(exp_timestamp - now_timestamp)

    if ttl_seconds > 0:
        # Guardamos en Redis -> Clave: 'blacklist:<token>' | Valor: 'revoked' | Expiración en segundos
        await redis.set(f"blacklist:{token}", "revoked", ex=ttl_seconds)


async def is_token_blacklisted(redis: Redis, token: str) -> bool:
    """
    Consulta en tiempo récord (sub-milisegundo) si un JWT fue revocado en Redis.
    """
    result = await redis.get(f"blacklist:{token}")
    return result is not None