"""
Módulo de Seguridad Central.

Proporciona utilidades para:
1. Hash y verificación de contraseñas mediante Bcrypt.
2. Generación y firma de JSON Web Tokens (JWT) para autenticación Stateless.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 1. Configuración del Contexto de Cifrado (Passlib)
# - schemes=["bcrypt"]: Define Bcrypt como el algoritmo estándar para hashing.
# - deprecated="auto": Marca automáticamente algoritmos antiguos como obsoletos si se cambian en el futuro.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Algoritmo de Firma JWT
# HMAC con SHA-256 (HS256) utiliza una clave secreta compartida (SECRET_KEY) para firmar los tokens.
ALGORITHM = "HS256"


# --- FUNCIONES PARA GESTIÓN DE CONTRASEÑAS ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con un hash almacenado en la BD.
    
    Returns:
        bool: True si coinciden, False en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Transforma una contraseña en texto plano en un hash irreversible usando Bcrypt.
    
    Nota: Bcrypt incluye automáticamente un 'Salt' aleatorio único para prevenir
    ataques de tablas Rainbow.
    """
    return pwd_context.hash(password)


# --- FUNCIONES PARA GESTIÓN DE TOKENS JWT ---

def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """
    Genera un Token de Acceso JWT firmado.

    Args:
        subject: Identificador principal del usuario (ej. ID o correo electrónico).
        expires_delta: Tiempo de vida personalizado para el token. Si no se provee,
                       se utiliza la configuración por defecto de settings.
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Claims del JWT (Carga útil / Payload)
    # - sub (subject): Sujeto del token (ID del usuario).
    # - exp (expiration time): Fecha/hora exacta de expiración en formato UNIX timestamp.
    # - iat (issued at): Fecha/hora de emisión.
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
    }

    # Codifica y firma el JWT con la clave secreta
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    return encoded_jwt