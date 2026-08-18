"""
Módulo de Excepciones Base del Core.
"""

from typing import Any
from fastapi import status


class AppException(Exception):
    """Excepción base para todos los errores de la aplicación."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "BAD_REQUEST",
        details: Any | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class UnauthorizedError(AppException):
    """Lanzada cuando la autenticación falla, expira o no es válida."""

    def __init__(
        self,
        message: str = "No autenticado o credenciales inválidas.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            details=details,
        )