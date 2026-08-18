"""Módulo de Excepciones del Dominio de Autenticación.

Define las excepciones específicas para los flujos de login local y Google OAuth.
"""

from typing import Any
from fastapi import status
from app.core.exceptions import AppException


class InvalidCredentialsError(AppException):
  """Lanzada cuando las credenciales ingresadas son incorrectas."""

  def __init__(
      self,
      message: str = "Correo electrónico o contraseña incorrectos.",
      details: Any | None = None,
  ):
    super().__init__(
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="INVALID_CREDENTIALS",
        details=details,
    )


class InactiveUserError(AppException):
  """Lanzada cuando el usuario intenta autenticarse pero su cuenta está deshabilitada."""

  def __init__(
      self,
      message: str = "La cuenta se encuentra inactiva o suspendida.",
      details: Any | None = None,
  ):
    super().__init__(
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="USER_INACTIVE",
        details=details,
    )


class InvalidGoogleTokenError(AppException):
  """Lanzada cuando el ID Token de Google no es válido o expiró."""

  def __init__(
      self,
      message: str = (
          "El token de Google es inválido, ha expirado o no se pudo verificar."
      ),
      details: Any | None = None,
  ):
    super().__init__(
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="INVALID_GOOGLE_TOKEN",
        details=details,
    )