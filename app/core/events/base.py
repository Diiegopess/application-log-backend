from datetime import datetime, timezone
from typing import Any, Dict
import uuid
from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    """Metadatos de auditoría y red asociados al evento."""
    ip_address: str = "unknown"
    user_agent: str = "unknown"
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class DomainEvent(BaseModel):
    """Estructura base inmutable para cualquier evento del sistema."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # Ej: 'auth.user_registered', 'auth.login_success'
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    payload: Dict[str, Any] = Field(default_factory=dict)