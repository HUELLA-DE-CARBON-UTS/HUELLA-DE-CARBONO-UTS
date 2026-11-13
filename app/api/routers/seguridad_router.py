"""Rutas del módulo MOD-02 Gestión de Seguridad (RolController)."""

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, responder
from app.api.schemas.seguridad import ConfiguracionRolEntrada
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.services.use_cases.configurar_rol import ConfigurarRol
from app.services.use_cases.verificar_permiso import SesionUsuario

router = APIRouter(prefix="/api/v1", tags=["MOD-02 Gestión de Seguridad"])

_ejemplo_error = {
    "estado": "error", "codigo": 422, "mensaje": "La configuración del rol no es válida", "datos": None,
    "errores": [{"campo": "permisos", "detalle": "La operación FUN-99 no existe en el sistema"}],
    "metadatos": {"funcionalidad": "FUN-11", "fecha": "2026-11-03T09:16:00-05:00"},
}


@router.put(
    "/roles/{nombreRol}",
    summary="HU-11 Crear un rol o reemplazar sus permisos",
    description=(
        "Crea el rol con estado «activo» y la lista de operaciones autorizadas o, si el rol ya existe, "
        "reemplaza completo su conjunto de permisos. Requiere una sesión vigente con el permiso FUN-11 (IC-01). "
        "Responde 201 si el rol se creó y 200 si se actualizó."
    ),
    response_model=RespuestaEstandar,
    status_code=201,
    responses={
        200: {"description": "Permisos del rol reemplazados"},
        401: {"description": "No hay una sesión vigente"},
        403: {"description": "El rol de la sesión no tiene el permiso FUN-11"},
        422: {"description": "Nombre vacío, sin permisos u operación inexistente",
              "content": {"application/json": {"example": _ejemplo_error}}},
        503: {"description": "No fue posible guardar la configuración del rol"},
    },
)
def configurar_rol(
    nombreRol: str = Path(..., description="Nombre del rol, por ejemplo «Analista ambiental»"),
    entrada: ConfiguracionRolEntrada = Body(...),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-11", "No tiene permiso para configurar roles")),
    db: Session = Depends(get_db),
):
    resultado = ConfigurarRol(RolRepositorioSQLAlchemy(db)).ejecutar(
        nombreRol, entrada.descripcion, entrada.permisos, sesion.documento)
    rol = resultado.rol
    datos = {
        "idRol": rol.id_rol, "nombre": rol.nombre, "descripcion": rol.descripcion,
        "estado": rol.estado, "permisos": rol.permisos, "accion": resultado.accion,
    }
    codigo = 201 if resultado.accion == "creado" else 200
    return responder(codigo, "Rol configurado correctamente", datos, funcionalidad="FUN-11")
