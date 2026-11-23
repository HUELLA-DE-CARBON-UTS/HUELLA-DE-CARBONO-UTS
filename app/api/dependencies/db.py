"""Sesión de base de datos por solicitud."""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.repositories.database.conexion import SessionLocal


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
