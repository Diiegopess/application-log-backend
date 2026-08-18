"""
Dependencias transversales de la API (Capa de Transporte HTTP).

Valida la firma de los tokens y extrae el identificador del usuario autenticado
sin consultar la base de datos ni depender de ningún modelo ORM de negocio.
"""

import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token

# Esquema OAuth2 Bearer para OpenAPI / Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    """
    Extrae y valida el JWT desde el header Authorization.
    
    Returns:
        uuid.UUID: Identificador único del usuario contenido en el claim 'sub'.
        
    Raises:
        UnauthorizedError: Si el token es inválido, expiró o el ID es corrupto.
    """
    try:
        payload = decode_token(token)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedError(
                message="Token malformado: falta identificador de usuario."
            )
        return uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise UnauthorizedError(
            message="Token de autenticación inválido, expirado o malformado."
        )