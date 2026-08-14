"""
Módulo de Excepciones Base del Core.

Define la clase base 'AppException' de la cual heredarán TODAS las
excepciones de dominio de la aplicación (Auth, Devices, Audits, etc.).
"""

from typing import Any, Optional


class AppException(Exception):
    """
    Excepción base para todos los errores de negocio de la aplicación.
    
    Permite que cualquier servicio levante una excepción con un mensaje claro,
    un código de estado HTTP adecuado y un código de error de texto predecible.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)