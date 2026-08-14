# app/users/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

from app.core.security import decode_access_token
from app.users import service as user_service
from app.users.models import User

from app.db.database import get_db

# Esquema OAuth2 para FastAPI / Swagger
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
  """Dependencia que valida el JWT y obtiene la instancia del usuario en la BD."""
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="No se pudieron validar las credenciales o el token ha expirado.",
      headers={"WWW-Authenticate": "Bearer"},
  )

  # 1. Decodificar payload
  payload = decode_access_token(token)
  if not payload:
    raise credentials_exception

  # 2. Extraer 'sub'
  user_id_str: str | None = payload.get("sub")
  if not user_id_str:
    raise credentials_exception

  # 3. Casteo seguro a entero
  try:
    user_id = int(user_id_str)
  except ValueError:
    raise credentials_exception

  # 4. Consultar BD
  user = await user_service.get_by_id(db, user_id=user_id)
  if not user:
    raise credentials_exception

  # 5. Validar estado de la cuenta
  if not user.is_active:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="La cuenta de usuario se encuentra inactiva o suspendida.",
    )

  return user