"""
Adaptador de Broker de Eventos basado en Redis Streams.

Implementa el contrato IEventPublisher para desacoplar los dominios
y permitir auditoría y sincronización asíncrona de datos.
"""

import json
import logging
from redis.asyncio import Redis
from app.core.events.base import DomainEvent
from app.core.events.interfaces import IEventPublisher

logger = logging.getLogger(__name__)


class RedisStreamPublisher(IEventPublisher):
    """Implementación de IEventPublisher utilizando Redis Streams (XADD)."""

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def publish(self, stream_or_topic: str, event: DomainEvent) -> str:
        """
        Publica un evento en el Stream indicado de Redis.
        
        Usa maxlen aproximado (~) para evitar que el stream crezca 
        indefinidamente en RAM una vez procesado por los workers.
        """
        try:
            # Serializamos el evento a un formato plano compatible con Redis Streams
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at,
                "metadata": json.dumps(event.metadata.model_dump()),
                "payload": json.dumps(event.payload)
            }

            # XADD stream_name * campo valor campo valor ...
            # maxlen=100000 mantiene un búfer rotativo en memoria
            message_id = await self.redis_client.xadd(
                name=stream_or_topic,
                fields=event_data,
                maxlen=100000,
                approximate=True
            )
            
            logger.info(
                f"[EVENT_PUBLISHED] {event.event_type} publicado en '{stream_or_topic}' con ID: {message_id}"
            )
            return str(message_id)
            
        except Exception as e:
            logger.error(
                f"[EVENT_PUBLISH_ERROR] Fallo al publicar {event.event_type} en '{stream_or_topic}': {str(e)}",
                exc_info=True
            )
            raise e