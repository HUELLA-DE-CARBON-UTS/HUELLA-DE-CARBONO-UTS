"""Dependencia que aplica IC-01 verificarPermiso a un endpoint."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import obtener_sesion
from app.api.dependencies.db import get_db
from app.services.use_cases.verificar_permiso import SesionUsuario, verificar_permiso


def requiere_permiso(operacion: str, mensaje: str):
    def dependencia(sesion: SesionUsuario = Depends(obtener_sesion), db: Session = Depends(get_db)) -> SesionUsuario:
        verificar_permiso(db, sesion, operacion, mensaje)
        return sesion
    return dependencia
