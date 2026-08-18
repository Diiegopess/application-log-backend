"""
Punto de Entrada Principal de la Aplicación (FastAPI).

Configura el ciclo de vida (lifespan), registra rutas de los dominios
(Auth, Users, Audit) y aplica los manejadores de excepciones globales.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.core.schemas import HealthCheckResponse
from app.infrastructure.brokers.redis_consumer import RedisStreamConsumer
from app.users.router import router as users_router


# ==============================================================================
# GESTOR DEL CICLO DE VIDA (LIFESPAN)
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestiona el inicio y parada ordenada de servicios auxiliares.
    Lanza el worker consumidor de Redis Streams en segundo plano.
    """
    # 1. Startup: Iniciar el consumidor de eventos en segundo plano
    consumer = RedisStreamConsumer()
    consumer_task = asyncio.create_task(consumer.start())

    yield  # La aplicación FastAPI recibe y procesa peticiones HTTP

    # 2. Shutdown: Detener el consumidor limpiamente al apagar el servidor
    await consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


# ==============================================================================
# INSTANCIA FASTAPI
# ==============================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar a tus dominios permitidos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar manejadores globales de excepciones
register_exception_handlers(app)

# ==============================================================================
# INCLUSIÓN DE ROUTERS POR DOMINIO
# ==============================================================================
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)


# ==============================================================================
# ENDPOINT DE HEALTH CHECK
# ==============================================================================
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Verificar salud de la API",
)
async def health_check():
    return HealthCheckResponse(
        status="ok",
        environment="development",
        version="1.0.0",
    )