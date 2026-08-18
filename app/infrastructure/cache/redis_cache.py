"""
Módulo de cliente de Redis para Operaciones en Memoria / Caché.

Maneja operaciones de ultra-baja latencia (sub-milisegundos) como:
- Rate Limiting
- Tokens OTP / 2FA temporales (con TTL)
- Blacklist de tokens y caché de sesiones
"""

from typing import AsyncGenerator
import redis.asyncio as redis
from app.core.config import settings

# Pool de conexiones compartido para optimizar recursos y reutilizar sockets
cache_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=20
)


def get_redis_cache_client() -> redis.Redis:
    """Retorna una instancia del cliente de Redis conectado al pool."""
    return redis.Redis(connection_pool=cache_pool)


async def get_redis_cache() -> AsyncGenerator[redis.Redis, None]:
    """
    Inyector de dependencia para FastAPI (Depends).
    Garantiza el uso del cliente dentro del contexto de una petición HTTP.
    """
    client = get_redis_cache_client()
    try:
        yield client
    finally:
        await client.aclose()


