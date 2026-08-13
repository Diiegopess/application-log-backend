"""
Punto de Entrada Principal de la Aplicación FastAPI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.core.database import Base, engine

# Importar los modelos para que SQLAlchemy 'sepa' que la tabla 'users' existe
# antes de llamar a create_all.
import app.users.models  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
  # CÓDIGO DE INICIO (STARTUP):
  # Crea las tablas definidas en los modelos si aún no existen en PostgreSQL
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  yield  # ⏸️ La aplicación queda corriendo y aceptando peticiones

  # CÓDIGO DE CIERRE (SHUTDOWN):
  # Aquí se pueden cerrar conexiones a bases de datos o clientes como Redis si es necesario.

app = FastAPI(
    title="App_Log API",
    version="1.0.0",
    description="API para la gestión de logs y autenticación de usuarios",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# Configuración de CORS (Cross-Origin Resource Sharing)
# Autoriza a las aplicaciones Frontend (React en puerto 5173 / 5174)
# ------------------------------------------------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],  # Permite cabeceras como Authorization, Content-Type, etc.
)

# Monta todos los endpoints bajo la versión 1 (/api/v1)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "API App_Log operativa correctamente"}