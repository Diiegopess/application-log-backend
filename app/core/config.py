from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Clase para leer y validar las variables de entorno del archivo .env."""

    # --- Proyecto ---
    PROJECT_NAME: str = "App_Log API"
    API_V1_STR: str = "/api/v1"

    # --- Seguridad y JWT ---
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Base de Datos Relacional (PostgreSQL) ---
    DATABASE_URL: str

    # --- Base de Datos en Memoria (Redis) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    
    GOOGLE_CLIENT_ID: str = ""


# Instancia única que importaremos en el resto del proyecto
settings = Settings()