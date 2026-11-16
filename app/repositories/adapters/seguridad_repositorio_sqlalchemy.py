"""Repositorios de MOD-02 Gestión de Seguridad con SQLAlchemy.

Ninguno confirma la transacción: lo hace el caso de uso o el contrato interno que los usa.
"""

from sqlalchemy.orm import Session

from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos import CredencialModelo


class CredencialRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def crear(self, documento: str, hash_contrasena: str, temporal: bool, id_rol: str) -> None:
        self.sesion.add(CredencialModelo(documento=documento, hash_contrasena=hash_contrasena, temporal=temporal,
                                         usada=False, id_rol=id_rol, fecha_actualizacion=ahora()))
        self.sesion.flush()
