"""
Punto de Entrada Principal de la Aplicación FastAPI.
"""

from fastapi import FastAPI
from app.api.api_router import api_router

app = FastAPI(
    title="App_Log API",
    version="1.0.0",
    description="API para la gestión de logs y autenticación de usuarios",
)

# Monta todos los endpoints bajo la versión 1 (/api/v1)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "API App_Log operativa correctamente"}