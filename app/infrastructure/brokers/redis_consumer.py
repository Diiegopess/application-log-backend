"""
Módulo de Consumo en Segundo Plano basado en Redis Streams.
"""

import asyncio
import json
import logging
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.audit.handlers import handle_audit_event
from app.auth.handlers import handle_user_created_by_admin_event
from app.core.config import settings
from app.core.events.base import DomainEvent, EventMetadata
from app.infrastructure.cache.redis_cache import get_redis_cache_client
from app.infrastructure.db.database import AsyncSessionLocal
from app.users.handlers import handle_user_registered_event

logger = logging.getLogger(__name__)


class RedisStreamConsumer:
    """Consumidor asíncrono para procesar eventos de dominio desde Redis Streams."""

    def __init__(self):
        self.redis: Redis = get_redis_cache_client()
        self.is_running: bool = False
        self.consumer_name: str = "fastapi_worker_1"

    async def _ensure_consumer_groups(self) -> None:
        """Crea los grupos de consumidores en el stream si aún no existen."""
        streams = [settings.AUTH_STREAM_NAME]
        groups = [settings.USERS_CONSUMER_GROUP, settings.AUDIT_CONSUMER_GROUP]

        for stream in streams:
            for group in groups:
                try:
                    await self.redis.xgroup_create(
                        name=stream, groupname=group, id="0", mkstream=True
                    )
                    logger.info(f"[CONSUMER_INIT] Grupo '{group}' creado en stream '{stream}'.")
                except ResponseError as e:
                    if "BUSYGROUP" in str(e):
                        pass
                    else:
                        logger.error(f"[CONSUMER_ERROR] Error al crear grupo {group}: {str(e)}")

    async def start(self) -> None:
        """Inicia el ciclo continuo de escucha y despacho de eventos."""
        await self._ensure_consumer_groups()
        self.is_running = True
        logger.info("[CONSUMER_STARTED] Worker de Redis Streams escuchando eventos...")

        while self.is_running:
            try:
                response = await self.redis.xreadgroup(
                    groupname=settings.USERS_CONSUMER_GROUP,
                    consumername=self.consumer_name,
                    streams={settings.AUTH_STREAM_NAME: ">"},
                    count=10,
                    block=2000,
                )

                if not response:
                    await asyncio.sleep(0.1)
                    continue

                for stream_name, messages in response:
                    for message_id, raw_data in messages:
                        await self._process_message(stream_name, message_id, raw_data)

            except asyncio.CancelledError:
                logger.info("[CONSUMER_STOPPING] Tarea de consumidor cancelada.")
                break
            except Exception as e:
                logger.error(f"[CONSUMER_LOOP_ERROR] Error en el ciclo de consumo: {str(e)}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_message(self, stream_name: str, message_id: str, raw_data: dict) -> None:
        """Parsea el evento y despacha a los manejadores correspondientes."""
        try:
            metadata_dict = json.loads(raw_data.get("metadata", "{}"))
            payload_dict = json.loads(raw_data.get("payload", "{}"))

            event = DomainEvent(
                event_id=raw_data.get("event_id"),
                event_type=raw_data.get("event_type"),
                occurred_at=raw_data.get("occurred_at"),
                metadata=EventMetadata(**metadata_dict),
                payload=payload_dict,
            )

            async with AsyncSessionLocal() as db:
                # 1. Auditoría: registra cronológicamente cualquier evento
                await handle_audit_event(event=event, db=db)

                # 2. Despacho a Users si viene de autoregistro
                if event.event_type == "auth.user_registered":
                    await handle_user_registered_event(event=event, db=db)

                # 3. Despacho a Auth si viene de creación administrativa
                elif event.event_type == "user.created_by_admin":
                    await handle_user_created_by_admin_event(event=event, db=db)

            # Confirmar procesamiento en Redis (XACK)
            await self.redis.xack(stream_name, settings.USERS_CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.error(
                f"[CONSUMER_PROCESS_ERROR] Fallo al procesar mensaje {message_id} en {stream_name}: {str(e)}",
                exc_info=True,
            )

    async def stop(self) -> None:
        """Detiene el consumidor y libera recursos de conexión."""
        self.is_running = False
        await self.redis.aclose()
        logger.info("[CONSUMER_STOPPED] Worker de Redis Streams apagado correctamente.")