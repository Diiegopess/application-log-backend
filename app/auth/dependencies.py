"""
Módulo de Dependencias para el Dominio de Autenticación.

Provee inyectores para:
- Extracción de metadatos de auditoría (IP del cliente y User-Agent).
- Instanciación del AuthService con la sesión de BD y el Broker inyectados.
"""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.core.events.base import EventMetadata
from app.core.events.interfaces import IEventPublisher
from app.infrastructure.brokers.factory import get_event_publisher
from app.infrastructure.db.database import get_db


def get_event_metadata(request: Request) -> EventMetadata:
    """
    Extrae la IP real y el User-Agent desde las cabeceras HTTP
    para trazabilidad y auditoría forense.
    """
    # 1. Resolver la IP real considerando proxies inversos / Cloudflare
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # El primer elemento de la lista es la IP original del cliente
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "unknown"

    # 2. Obtener el User-Agent
    user_agent = request.headers.get("user-agent", "unknown")

    return EventMetadata(
        ip_address=client_ip,
        user_agent=user_agent
    )


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    publisher: IEventPublisher = Depends(get_event_publisher),
) -> AuthService:
    """
    Inyector de dependencia que construye el AuthService con
    la sesión de BD y el publicador de eventos listos.
    """
    return AuthService(db=db, publisher=publisher)