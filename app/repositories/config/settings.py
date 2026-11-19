import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Huella de Carbono UTS")
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = os.getenv("APP_DEBUG", "True").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL") or f"sqlite:///{(RAIZ / 'dev.db').as_posix()}"
    secret_key: str = os.getenv("SECRET_KEY", "")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    token_admin_inicial: str = os.getenv("TOKEN_ADMIN_INICIAL", "")
    documento_admin_inicial: str = os.getenv("DOCUMENTO_ADMIN_INICIAL", "1000000000")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_usuario: str = os.getenv("SMTP_USUARIO", "")
    smtp_contrasena: str = os.getenv("SMTP_CONTRASENA", "")
    correo_remitente: str = os.getenv("CORREO_REMITENTE", "no-responder@huella-carbono.local")


settings = Settings()
