"""
Dependencias transversales de la API (Capa de Transporte HTTP).

Valida la firma de los tokens y extrae el identificador del usuario autenticado
sin consultar la base de datos ni depender de ningún modelo ORM de negocio.
"""

import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.schemas import TokenPayload
from app.core.security import decode_access_token

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
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError(message="Token inválido o expirado.")

    try:
        token_data = TokenPayload(**payload)
        if not token_data.sub:
            raise UnauthorizedError(
                message="Token malformado: falta identificador de usuario."
            )
        # Parseo seguro a UUID
        user_id = uuid.UUID(token_data.sub)
    except (ValidationError, ValueError, TypeError):
        raise UnauthorizedError(
            message="Identificador de usuario inválido en el token."
        )

    return user_id