from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.seguridad import ConfiguracionRolEntrada
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.services.use_cases.configurar_rol import ConfigurarRol
from app.services.mappers import api

router = APIRouter(prefix="/api/v1", tags=["MOD-02 Gestión de Seguridad"])
SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


@router.put(
    "/roles/{roleName}",
    summary="HU-11 Crear un rol o reemplazar sus permisos",
    description="Crea el rol con estado «active» y la lista de operaciones autorizadas o, si el rol ya existe, "
                "reemplaza completo su conjunto de permisos. Requiere el permiso FUN-11 (IC-01). "
                "Responde 201 si el rol se creó y 200 si se actualizó.",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-11", "No fue posible guardar la configuración del rol"),
    responses={
        200: {"description": "Permisos del rol reemplazados"},
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-11"},
        422: ejemplo(422, "La configuración del rol no es válida", None,
                     [{"field": "permissions", "detail": "La operación FUN-99 no existe en el sistema"}], "FUN-11"),
        503: {"description": "No fue posible guardar la configuración del rol"},
    },
)
def configurar_rol(
    roleName: str = Path(..., description="Nombre del rol, por ejemplo «Analista ambiental»"),
    entrada: ConfiguracionRolEntrada = Body(...),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-11", "No tiene permiso para configurar roles")),
    db: Session = Depends(get_db),
):
    resultado = ConfigurarRol(RolRepositorioSQLAlchemy(db)).ejecutar(
        roleName, entrada.description, entrada.permissions, sesion.documento)
    rol = resultado.rol
    datos = {
        "roleId": rol.id_rol, "name": rol.nombre, "description": rol.descripcion,
        "status": api.estado(rol.estado), "permissions": rol.permisos, "action": api.accion(resultado.accion),
    }
    codigo = 201 if resultado.accion == "creado" else 200
    return responder(codigo, "Rol configurado correctamente", datos, funcionalidad="FUN-11")
