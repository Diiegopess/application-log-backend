"""
Módulo de Excepciones del Dominio de Autenticación.

Define las excepciones específicas para flujos de login local,
Google OAuth, estado de cuenta y validación de tokens.
"""

from fastapi import status
from app.core.exceptions import AppException


class InvalidCredentialsError(AppException):
    """Lanzada cuando el usuario o la contraseña local no coinciden."""
    def __init__(self, message: str = "Correo electrónico o contraseña incorrectos."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
        )


class InactiveUserError(AppException):
    """Lanzada cuando un usuario intenta iniciar sesión pero su cuenta está deshabilitada."""
    def __init__(self, message: str = "La cuenta de usuario se encuentra inactiva o suspendida."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,  # 403 Forbidden es más semántico para cuentas bloqueadas
            error_code="USER_INACTIVE",
        )


class InvalidGoogleTokenError(AppException):
    """Lanzada cuando el token de Google es inválido, expiró o no pudo ser verificado."""
    def __init__(self, message: str = "El token de Google es inválido, ha expirado o no se pudo verificar."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_GOOGLE_TOKEN",
        )