"""
Módulo de Manejadores Centralizados de Excepciones.

Captura cualquier excepción lanzada en la aplicación y la transforma
en una respuesta JSON estándar y predecible hacia el cliente.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException

# Configuramos un logger para registrar errores en consola
logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registra todos los Exception Handlers en la instancia de FastAPI.
    """

    # --------------------------------------------------------------------------
    # 1. Manejador para nuestras Excepciones de Dominio (AppException)
    # --------------------------------------------------------------------------
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            f"[{exc.error_code}] {request.method} {request.url.path} - {exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    # --------------------------------------------------------------------------
    # 2. Manejador para Errores de Validación de Pydantic (Campos mal enviados)
    # --------------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Simplificamos los errores de Pydantic para que el frontend los entienda fácil
        errors = [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", []) if loc != "body"),
                "issue": err.get("msg"),
            }
            for err in exc.errors()
        ]
        
        logger.warning(
            f"[VALIDATION_ERROR] {request.method} {request.url.path} - {errors}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Los datos enviados en la petición no son válidos.",
                    "details": errors,
                },
            },
        )

    # --------------------------------------------------------------------------
    # 3. Manejador para Errores Inesperados del Sistema (500)
    # --------------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Registramos el traceback completo en logs para auditoría interna
        logger.error(
            f"[UNHANDLED_EXCEPTION] Error no controlado en {request.method} {request.url.path}",
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Ha ocurrido un error inesperado en el servidor.",
                    "details": None,
                },
            },
        )