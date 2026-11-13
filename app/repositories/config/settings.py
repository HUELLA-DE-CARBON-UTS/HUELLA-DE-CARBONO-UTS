"""Configuración de la aplicación leída desde el archivo .env."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Huella de Carbono UTS")
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = os.getenv("APP_DEBUG", "True").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL") or "sqlite:///./dev.db"
    secret_key: str = os.getenv("SECRET_KEY", "")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    # Sesión del administrador inicial. Se usa mientras no exista el inicio de
    # sesión (HU-06); después se reemplaza por las sesiones reales.
    token_admin_inicial: str = os.getenv("TOKEN_ADMIN_INICIAL", "")
    documento_admin_inicial: str = os.getenv("DOCUMENTO_ADMIN_INICIAL", "1000000000")


settings = Settings()
