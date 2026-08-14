"""
Agregador Central de Rutas de la API.

Importa y centraliza los routers de cada dominio.
"""

from fastapi import APIRouter
from app.users.router import router as users_router
from app.auth.router import router as auth_router  

# Router principal
api_router = APIRouter()

# Inclusión de routers por dominio
api_router.include_router(users_router)
api_router.include_router(auth_router)