import re

from sqlalchemy.orm import Session

from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import CredencialRepositorioSQLAlchemy
from app.services.seguridad.contrasenas import generar_hash, generar_temporal

FORMATO_ID_ROL = re.compile(r"^ROL-\d+$", re.IGNORECASE)


def consultar_rol(db: Session, referencia: str):
    """Busca el rol por identificador (ROL-04) o por nombre."""
    repo = RolRepositorioSQLAlchemy(db)
    referencia = " ".join((referencia or "").split())
    if FORMATO_ID_ROL.match(referencia):
        return repo.buscar_por_id(referencia.upper())
    return repo.buscar_por_nombre(referencia)


def registrar_credenciales_y_rol(db: Session, documento: str, id_rol: str) -> str:
 
    temporal = generar_temporal()
    CredencialRepositorioSQLAlchemy(db).crear(documento, generar_hash(temporal), temporal=True, id_rol=id_rol)
    return temporal
