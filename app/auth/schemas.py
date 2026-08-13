"""
Módulo de Esquemas Pydantic v2 para el Dominio de Autenticación.

Define las reglas de validación y los contratos de datos
para el login local, autenticación con Google y la emisión/decodificación de JWT.
"""

from pydantic import BaseModel, EmailStr, Field


# --- 1. CONTRATO DE ENTRADA: LOGIN LOCAL ---
class LoginRequest(BaseModel):
    """
    DTO para la autenticación estándar con credenciales de la aplicación.
    Recibe el correo y la contraseña en texto plano para su verificación en la BD.
    """

    email: EmailStr = Field(
        ...,
        description="Correo electrónico registrado del usuario",
        examples=["usuario@ejemplo.com"],
    )
    password: str = Field(
        ...,
        description="Contraseña en texto plano ingresada en el formulario",
    )


# --- 2. CONTRATO DE ENTRADA: GOOGLE OAUTH 2.0 ---
class GoogleAuthRequest(BaseModel):
    """
    DTO para la autenticación delegada con Google.
    
    El cliente/frontend (React, Flutter, etc.) completa el inicio de sesión
    en el cliente de Google y nos envía el ID Token firmado devuelto por Google.
    """

    id_token: str = Field(
        ...,
        description="ID Token JWT emitido y firmado por Google",
    )


# --- 3. CONTRATO DE SALIDA: RESPUESTA DE AUTENTICACIÓN ---
class TokenResponse(BaseModel):
    """
    DTO público de respuesta entregado al cliente tras un login exitoso (Local o Google).
    
    Cumple con el estándar de autorización OAuth 2.0.
    """

    access_token: str = Field(
        ...,
        description="Token de acceso firmado en formato JWT",
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token emitido según el esquema Bearer Auth",
    )


# --- 4. ESTRUCTURA INTERNA: PAYLOAD DEL JWT ---
class TokenPayload(BaseModel):
    """
    Modelo de validación para el contenido decodificado del JWT.
    
    Representa los 'claims' guardados dentro de la firma digital del token.
    """

    sub: str | None = None  # Subject: Guarda el ID del usuario en formato String (ej: "12")
    exp: int | None = None  # Expiration: Timestamp UNIX en el que caduca el token


