"""
Módulo de Dependencias para el Dominio de Auditoría.
"""

from fastapi import Depends
from app.users.dependencies import get_current_superuser
from app.users.models import User


async def require_audit_access(
    current_admin: User = Depends(get_current_superuser),
) -> User:
    """
    Garantiza que solo administradores o auditores autorizados
    puedan acceder al registro de eventos del sistema.
    """
    return current_admin