"""
Módulo de Modelos SQLAlchemy para el Dominio de Usuarios.

Define la estructura física de la tabla 'users' en PostgreSQL,
soportando autenticación local (Email/Password) y OAuth 2.0 (Google).
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- CAMBIO 1: Contraseña Opcional ---
    # `nullable=True` porque los usuarios que se registran vía Google no tienen contraseña en nuestra BD.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- CAMBIO 2: Datos de Proveedor OAuth ---
    # Guarda el ID único que otorga Google (ej. "10923840293840").
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    # Guarda la foto de perfil traída desde la cuenta de Google
    picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )