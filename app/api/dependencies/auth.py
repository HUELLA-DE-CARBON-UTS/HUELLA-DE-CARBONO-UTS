from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.domain.exceptions.errores import PermisoDenegado, SesionNoValida
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import (
    CredencialRepositorioSQLAlchemy, SesionRepositorioSQLAlchemy)
from app.services.use_cases.verificar_permiso import SesionUsuario

esquema_bearer = HTTPBearer(auto_error=False, description="Token recibido en la cabecera X-Token-Sesion al iniciar sesión")

SIN_SESION = SesionNoValida("No hay una sesión vigente", [
    {"field": "session", "detail": "Debe iniciar sesión para realizar esta operación"},
])


def obtener_sesion(credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
                   db: Session = Depends(get_db)) -> SesionUsuario:
    if credenciales is None or not credenciales.credentials:
        raise SIN_SESION
    sesion = SesionRepositorioSQLAlchemy(db).buscar_por_token(credenciales.credentials)
    if sesion is None or sesion.estado != "vigente":
        raise SIN_SESION
    if sesion.requiere_cambio_contrasena:
        raise PermisoDenegado("Debe cambiar la contraseña temporal antes de continuar", [
            {"field": "session", "detail": "La sesión se creó con una credencial temporal"}])
    credencial = CredencialRepositorioSQLAlchemy(db).buscar(sesion.documento)
    return SesionUsuario(documento=sesion.documento, rol=credencial.nombre_rol)
