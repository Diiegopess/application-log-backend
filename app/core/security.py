"""
Módulo de Seguridad Central.

Proporciona utilidades para:
1. Hash y verificación de contraseñas mediante Bcrypt.
2. Generación y firma de JSON Web Tokens (JWT) para autenticación Stateless.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt  # 👈 Importamos JWTError
from passlib.context import CryptContext

from app.core.config import settings

# 1. Configuración del Contexto de Cifrado (Passlib)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Algoritmo de Firma JWT
ALGORITHM = "HS256"


# --- FUNCIONES PARA GESTIÓN DE CONTRASEÑAS ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con un hash almacenado en la BD.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Transforma una contraseña en texto plano en un hash irreversible usando Bcrypt.
    """
    return pwd_context.hash(password)


# --- FUNCIONES PARA GESTIÓN DE TOKENS JWT ---

def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """
    Genera un Token de Acceso JWT firmado.
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
    }

    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decodifica un JWT firmado y retorna su payload sin tocar la BD.
    
    Returns:
        dict: Payload con las claims del token si es válido.
        None: Si el token es inválido, fue alterado o expiró.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:  # 👈 Específico para errores de firma, expiración o formato JWT
        return None