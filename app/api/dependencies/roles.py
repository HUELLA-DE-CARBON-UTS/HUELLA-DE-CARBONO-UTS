from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SIN_SESION, SesionUsuario, sesion_del_token
from app.api.dependencies.db import get_db
from app.api.schemas.respuesta import datos_de_ruta
from app.domain.entities.sesion import Sesion
from app.domain.exceptions.errores import ErrorNegocio, PermisoDenegado, ServicioNoDisponible
from app.services.contratos.ic01_verificar_permiso import verificar_permiso


def requiere_permiso(operacion: str, mensaje_403: str):

    def dependencia(request: Request, sesion: Sesion = Depends(sesion_del_token), db: Session = Depends(get_db)) -> SesionUsuario:
        resultado = verificar_permiso(db, sesion.id_sesion, operacion)
        codigo = resultado["status"]
        if codigo == 200:
            return SesionUsuario(id_sesion=sesion.id_sesion, documento=sesion.documento)
        if codigo == 401:
            raise SIN_SESION
        if codigo == 403:
            raise PermisoDenegado(mensaje_403, [{"field": "session", "detail": resultado["errors"][0]["detail"]}])
        if codigo == 503:
            mensaje = datos_de_ruta(request).get("x-mensaje-503", resultado["message"])
            raise ServicioNoDisponible(mensaje, resultado["errors"])
        raise ErrorNegocio(resultado["message"], resultado["errors"])

    return dependencia
