from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.domain.entities.sesion import Sesion
from app.domain.exceptions.errores import SesionNoValida
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import SesionRepositorioSQLAlchemy

esquema_bearer = HTTPBearer(auto_error=False, description="Token recibido en la cabecera X-Token-Sesion al iniciar sesión")

SIN_SESION = SesionNoValida("No hay una sesión vigente", [
    {"field": "session", "detail": "Debe iniciar sesión para realizar esta operación"},
])


@dataclass
class SesionUsuario:
    id_sesion: str
    documento: str


def sesion_del_token(credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
                     db: Session = Depends(get_db)) -> Sesion:
    if credenciales is None or not credenciales.credentials:
        raise SIN_SESION
    sesion = SesionRepositorioSQLAlchemy(db).buscar_por_token(credenciales.credentials)
    if sesion is None:
        raise SIN_SESION
    return sesion
