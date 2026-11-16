"""Motor de base de datos y fábrica de sesiones de SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.repositories.config.settings import settings


class Base(DeclarativeBase):
    pass


def crear_motor(url: str):
    argumentos = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=argumentos)


engine = crear_motor(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
