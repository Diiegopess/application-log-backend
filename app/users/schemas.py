"""
Módulo de Esquemas Pydantic v2 para el Dominio de Usuarios.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- 1. ESQUEMA BASE (Atributos Compartidos) ---
class UserBase(BaseModel):
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


# --- 2. ESQUEMA PARA CREACIÓN ADMINISTRATIVA DE USUARIOS ---
class UserCreateAdmin(BaseModel):
    """Esquema de entrada para que un administrador registre usuarios con credenciales iniciales."""

    email: EmailStr
    password: str = Field(..., min_length=6, description="Contraseña inicial del usuario")
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


# --- 3. ESQUEMA PARA CREACIÓN INTERNA DE PERFIL ---
class UserProfileCreate(BaseModel):
    id: uuid.UUID = Field(
        ...,
        description="UUID asignado previamente en auth_credentials",
    )
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


# --- 4. ESQUEMA PARA ACTUALIZACIÓN DE PERFIL (PATCH/PUT) ---
class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None)


# --- 5. ESQUEMA PARA ACTUALIZACIÓN ADMINISTRATIVA ---
class UserUpdateAdmin(UserUpdate):
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(
        default=None,
        description="Permite otorgar o revocar permisos de superusuario",
    )


# --- 6. ESQUEMA DE RESPUESTA DE LA API ---
class UserResponse(UserBase):
    id: uuid.UUID
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)