"""
Módulo de cliente para la base de datos en memoria (Redis).

Redis se utiliza para operaciones ultrarrápidas (latencia de sub-milisegundos) 
como la gestión de caché, control de tasa de peticiones (Rate Limiting) 
y almacenamiento de tokens de un solo uso (OTP/2FA).
"""

from redis.asyncio import Redis
from app.core.config import settings

# 1. Instancia Global del Cliente Asíncrono de Redis
# Usamos `redis.asyncio` para realizar llamadas no bloqueantes hacia Redis.
# - settings.REDIS_URL: Lee la URL de conexión (ej. redis://localhost:6379/0).
# - encoding="utf-8": Define la codificación de texto estándar.
# - decode_responses=True: Por defecto, Redis devuelve respuestas en formato de bytes (b'admin').
#   Al activar esta opción, Redis convierte automáticamente las respuestas a cadenas de texto (str) de Python,
#   haciendo el código mucho más limpio y fácil de manipular.
redis_client: Redis = Redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


# 2. Inyector de Dependencia de Redis (get_redis)
# Permite inyectar la conexión activa de Redis en cualquier router o servicio
# mediante la inyección de dependencias de FastAPI: `redis: Redis = Depends(get_redis)`.
async def get_redis() -> Redis:
    """Retorna la instancia global del cliente de Redis listo para operaciones asíncronas."""
    return redis_client