from typing import Protocol
from app.core.events.base import DomainEvent


class IEventPublisher(Protocol):
    """Contrato abstracto para publicar eventos a cualquier broker."""
    
    async def publish(self, stream_or_topic: str, event: DomainEvent) -> str:
        """
        Publica un evento de dominio.
        Retorna el ID asignado por el broker (ej. ID del stream de Redis).
        """
        ...


class IEventConsumer(Protocol):
    """Contrato abstracto para escuchar y procesar eventos."""
    
    async def start_listening(self) -> None:
        """Inicia el ciclo de consumo en segundo plano."""
        ...