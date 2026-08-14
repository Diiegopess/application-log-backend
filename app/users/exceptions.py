"""
Módulo de Excepciones del Dominio de Usuarios.

Define los errores específicos para la gestión, consulta y actualización de usuarios.
"""

from fastapi import status
from app.core.exceptions import AppException


class UserNotFoundError(AppException):
    """Lanzada cuando se consulta o actualiza un usuario que no existe."""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"El usuario con ID {user_id} no existe.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
        )


class EmailAlreadyExistsError(AppException):
    """Lanzada cuando se intenta registrar o actualizar con un email ya en uso."""
    def __init__(self, email: str):
        super().__init__(
            message=f"El correo electrónico '{email}' ya se encuentra registrado.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EMAIL_ALREADY_EXISTS",
        )