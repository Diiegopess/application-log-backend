
#Punto de Entrada Principal de la Aplicación FastAPI.


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api_router import api_router
from app.db.database import Base, engine
from app.core.handlers import register_exception_handlers

# Importamos los modelos para que el 'metadata' de SQLAlchemy los reconozca
# y pueda generar las tablas automáticamente durante el evento de inicio.
import app.users.models  # noqa: F401


# ==============================================================================
# 1. GESTIÓN DEL CICLO DE VIDA (LIFESPAN)
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Administra los eventos de inicio (startup) y apagado (shutdown) del servidor.
    Reemplaza los antiguos eventos '@app.on_event("startup")' de versiones previas.
    """
    # --------------------------------------------------------------------------
    # FASE DE INICIO: Se ejecuta una sola vez antes de recibir peticiones
    # --------------------------------------------------------------------------
    async with engine.begin() as conn:
        # Crea las tablas en PostgreSQL si aún no existen
        await conn.run_sync(Base.metadata.create_all)

    yield  # ⏸️ El servidor queda activo y listo para atender solicitudes HTTP

    # --------------------------------------------------------------------------
    # FASE DE CIERRE: Se ejecuta de forma segura cuando se detiene el contenedor
    # --------------------------------------------------------------------------
    # Liberar conexiones activas de PostgreSQL y Redis al apagar
    await engine.dispose()


# ==============================================================================
# 2. INSTANCIA PRINCIPAL DE FASTAPI
# ==============================================================================
app = FastAPI(
    title="App_Log API",
    version="1.0.0",
    description="API para la gestión de logs, hardening y autenticación de usuarios.",
    lifespan=lifespan,
)


# ==============================================================================
# 3. POLÍTICA DE SEGURIDAD CORS (Cross-Origin Resource Sharing)
# ==============================================================================
# Define qué orígenes (direcciones de frontend) tienen permiso para consumir la API
origins = [
    "http://localhost:5173",  # Servidor de desarrollo local (Vite/React)
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Dominios autorizados
    allow_credentials=True,      # Permite envío de cookies y cabeceras de autorización
    allow_methods=["*"],         # Permite todos los verbos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],         # Permite todas las cabeceras estándar y personalizadas
)


# ==============================================================================
# 4. MANEJO CENTRALIZADO DE EXCEPCIONES
# ==============================================================================
# Intercepta cualquier AppException o error imprevisto y devuelve respuestas JSON uniformes
register_exception_handlers(app)


# ==============================================================================
# 5. MONTAJE DE RUTAS Y HEALTH CHECK
# ==============================================================================
# Monta todas las rutas de negocio bajo el prefijo global /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health Check"])
async def root():
    """
    Endpoint base para verificar la disponibilidad inmediata del servicio.
    """
    return {
        "status": "healthy",
        "message": "API App_Log operativa correctamente",
        "version": "1.0.0",
    }