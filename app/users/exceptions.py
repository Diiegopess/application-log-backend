"""
Módulo de Excepciones del Dominio de Usuarios.
"""

from typing import Any
from fastapi import status
from app.core.exceptions import AppException


class UserNotFoundError(AppException):
    """Lanzada cuando un usuario no existe en la base de datos."""

    def __init__(
        self,
        message: str = "El usuario solicitado no fue encontrado.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
            details=details,
        )


class UserAlreadyExistsError(AppException):
    """Lanzada cuando se intenta crear o actualizar un usuario con un email duplicado."""

    def __init__(
        self,
        message: str = "Ya existe un usuario registrado con este correo electrónico.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_ALREADY_EXISTS",
            details=details,
        )