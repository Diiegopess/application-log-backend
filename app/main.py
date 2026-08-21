"""
Punto de Entrada Principal de la Aplicación (FastAPI).
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


from app.infrastructure.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Crear tablas y generar superusuario
    await init_db()

    # Startup: Iniciar consumidor de Redis Streams
    consumer = RedisStreamConsumer()
    consumer_task = asyncio.create_task(consumer.start())

    yield

    # Shutdown
    await consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass



app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_exception_handlers(app)


app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)



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