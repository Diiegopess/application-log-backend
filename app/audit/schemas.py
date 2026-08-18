"""
Módulo de Esquemas Pydantic v2 para el Dominio de Auditoría.
"""

from datetime import datetime
from typing import Any, Dict
import uuid
from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    """Esquema interno utilizado por los Event Handlers para insertar logs."""

    event_id: str
    event_type: str
    user_id: uuid.UUID | None = None
    ip_address: str = "unknown"
    user_agent: str = "unknown"
    correlation_id: str | None = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


class AuditLogResponse(BaseModel):
    """Esquema público retornado en endpoints administrativos de auditoría."""

    id: uuid.UUID
    event_id: str
    event_type: str
    user_id: uuid.UUID | None
    ip_address: str
    user_agent: str
    correlation_id: str | None
    payload: Dict[str, Any]
    occurred_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)