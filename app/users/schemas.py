"""
Módulo de Esquemas Pydantic v2 para el Dominio de Usuarios.

Define las reglas de validación y serialización de datos
para la entrada y salida de la API en las operaciones del usuario.
"""

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
        default=True, description="Indica si la cuenta se encuentra activa"
    )


# --- 2. ESQUEMA PARA CREACIÓN LOCAL (Email + Contraseña) ---
class UserCreate(UserBase):
    """Esquema para el registro de usuarios mediante credenciales locales."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contraseña en texto plano (mínimo 8 caracteres)",
    )


# --- 3. ESQUEMA PARA CREACIÓN VÍA GOOGLE OAUTH ---
class UserCreateGoogle(UserBase):
    """Esquema interno para el registro o actualización automática vía Google OAuth 2.0."""

    google_id: str = Field(..., description="ID único entregado por Google")
    picture_url: str | None = Field(
        default=None, description="URL de la imagen de perfil de Google"
    )


# --- 4. ESQUEMA PARA ACTUALIZACIÓN (PATCH/PUT) ---
class UserUpdate(BaseModel):
    """Esquema de campos opcionales para actualizar la información de un usuario."""

    email: EmailStr | None = Field(default=None)
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = Field(default=None)


# --- 5. ESQUEMA DE RESPUESTA DE LA API (Response Model) ---
class UserResponse(UserBase):
    """
    Esquema público retornado por la API hacia los clientes HTTP.
    
    Excluye campos sensibles como 'hashed_password'.
    """

    id: int
    is_superuser: bool
    google_id: str | None = None
    picture_url: str | None = None
    created_at: datetime
    updated_at: datetime

    # Configuración de Pydantic v2
    # from_attributes=True permite que Pydantic lea directamente las instancias de modelos de SQLAlchemy.
    model_config = ConfigDict(from_attributes=True) 

    # --- 6. ESQUEMA PARA ACTUALIZACIÓN POR PARTE DE UN ADMINISTRADOR ---
class UserUpdateAdmin(UserUpdate):
    """
    Esquema extendido para que los administradores puedan actualizar 
    roles o permisos privilegiados como 'is_superuser'.
    """

    is_superuser: bool | None = Field(
        default=None, 
        description="Permite otorgar o revocar permisos de superusuario"
    )