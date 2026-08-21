import logging
import uuid
from sqlalchemy import select

from app.audit.models import AuditLog  # Registra la tabla 'audit_logs'
from app.auth.models import AuthCredential  # Registra la tabla 'auth_credentials'
from app.core.config import settings
from app.core.security import hash_password
from app.infrastructure.db.database import AsyncSessionLocal, Base, engine
from app.users.models import User  # Registra la tabla 'users'

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Crea las tablas pendientes en la base de datos y genera el superusuario inicial.
    """
    # 1. Crear tablas si no existen (DDL inicial)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tablas de la base de datos verificadas/creadas exitosamente.")

    # 2. Seeding de superusuario inicial
    async with AsyncSessionLocal() as session:
        try:
            stmt_cred = select(AuthCredential).where(
                AuthCredential.email == settings.FIRST_SUPERUSER_EMAIL
            )
            res_cred = await session.execute(stmt_cred)
            existing_cred = res_cred.scalar_one_or_none()

            if existing_cred:
                logger.info(
                    f"Superusuario inicial ya registrado: {settings.FIRST_SUPERUSER_EMAIL}"
                )
                return

            user_id = uuid.uuid4()

            # Crear credencial de autenticación
            cred = AuthCredential(
                id=user_id,
                email=settings.FIRST_SUPERUSER_EMAIL,
                password_hash=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
                is_email_verified=True,
            )
            session.add(cred)

            # Crear perfil de usuario con permisos de superusuario
            user_profile = User(
                id=user_id,
                email=settings.FIRST_SUPERUSER_EMAIL,
                full_name=settings.FIRST_SUPERUSER_FULL_NAME,
                is_active=True,
                is_superuser=True,
            )
            session.add(user_profile)

            await session.commit()
            logger.info(
                f"Superusuario inicial creado exitosamente: {settings.FIRST_SUPERUSER_EMAIL}"
            )

        except Exception as e:
            await session.rollback()
            logger.error(f"Error al ejecutar el seed del superusuario: {e}")
            raise