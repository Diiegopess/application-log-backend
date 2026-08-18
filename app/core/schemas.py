"""
Módulo de Esquemas Transversales (Core).

Define los contratos y DTOs agnósticos utilizados por toda la aplicación,
tales como la estructura del JWT, respuestas estándar y mensajes comunes.
"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

# Tipo genérico para respuestas estructuradas
T = TypeVar("T")


# --- ESQUEMAS DE AUTENTICACIÓN Y SEGURIDAD ---

class TokenPayload(BaseModel):
    """
    Representación estructurada de los claims contenidos dentro del JWT.
    Agnóstico de la base de datos o modelos ORM.
    """
    sub: str | None = Field(default=None, description="Identificador único del sujeto (User ID)")
    exp: int | None = Field(default=None, description="Timestamp UNIX de expiración del token")
    iat: int | None = Field(default=None, description="Timestamp UNIX de emisión del token")

    model_config = ConfigDict(extra="ignore")


# --- ESQUEMAS DE RESPUESTAS ESTÁNDAR ---

class MessageResponse(BaseModel):
    """Esquema genérico para respuestas de confirmación o mensajes simples."""
    message: str = Field(..., description="Mensaje informativo de la operación")


class HealthCheckResponse(BaseModel):
    """Esquema para verificar el estado de la API."""
    status: str = Field(default="ok", description="Estado del servicio")
    environment: str = Field(..., description="Entorno de ejecución (development, production, etc.)")
    version: str = Field(default="1.0.0", description="Versión de la API")


# --- ESQUEMA GENÉRICO PARA RESPUESTAS ENVOLVENTES (Opcional) ---

class ApiResponse(BaseModel, Generic[T]):
    """
    Contenedor estándar para respuestas exitosas.
    Útil si tu API maneja una estructura uniforme tipo:
    { "success": true, "data": { ... }, "error": null }
    """
    success: bool = True
    data: T | None = None
    message: str | None = None