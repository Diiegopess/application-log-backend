"""
Módulo de Inyección de Dependencias para el Dominio de Usuarios.

Proporciona resolvedores de dependencias para FastAPI, encargados de
extraer el token Bearer, validar la firma y recuperar la entidad User activa.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.core.security import decode_access_token
from app.users import service as user_service
from app.users.models import User

# Esquema OAuth2 Bearer que indica a Swagger y a FastAPI de dónde extraer el token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Inyector de dependencia para rutas protegidas.

    Decodifica el JWT, extrae el ID del usuario y consulta la base de datos
    para retornar la instancia del usuario autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o el token ha expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decodifica el token sin tocar la BD
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    # 2. Extrae el ID del usuario del claim 'sub'
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # 3. Consulta la base de datos
    user = await user_service.get_by_id(db, user_id=int(user_id))
    if not user:
        raise credentials_exception

    # 4. Verifica el estado de la cuenta
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de usuario se encuentra inactiva o suspendida.",
        )

    return user