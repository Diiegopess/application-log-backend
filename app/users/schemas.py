"""
Módulo de Esquemas Pydantic v2 para el Dominio de Usuarios.

Define las reglas de validación y serialización de datos
para la entrada y salida de la API en la gestión de perfiles de usuario.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- 1. ESQUEMA BASE (Atributos Compartidos) ---
class UserBase(BaseModel):
    """Atributos comunes que comparten otros esquemas de usuario."""

    email: EmailStr = Field(
        ...,
        description="Correo electrónico válido del usuario",
        examples=["usuario@ejemplo.com"],
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Nombre completo opcional del usuario",
    )
    is_active: bool = Field(
        default=True,
        description="Indica si el perfil se encuentra habilitado",
    )


# --- 2. ESQUEMA PARA CREACIÓN INTERNA DE PERFIL ---
class UserProfileCreate(BaseModel):
    """Esquema utilizado para aprovisionar el perfil de un usuario vinculado a Auth."""

    id: uuid.UUID = Field(
        ...,
        description="UUID asignado previamente en auth_credentials",
    )
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


# --- 3. ESQUEMA PARA ACTUALIZACIÓN DE PERFIL (PATCH/PUT) ---
class UserUpdate(BaseModel):
    """Esquema de campos permitidos para que el usuario actualice su propio perfil."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None)


# --- 4. ESQUEMA PARA ACTUALIZACIÓN ADMINISTRATIVA ---
class UserUpdateAdmin(UserUpdate):
    """Esquema extendido para que un administrador modifique roles y estados."""

    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(
        default=None,
        description="Permite otorgar o revocar permisos de superusuario",
    )


# --- 5. ESQUEMA DE RESPUESTA DE LA API (Response Model) ---
class UserResponse(UserBase):
    """
    Esquema público retornado por la API hacia los clientes HTTP.
    
    Alineado estrictamente con el modelo SQLAlchemy de 'users'.
    """

    id: uuid.UUID
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)