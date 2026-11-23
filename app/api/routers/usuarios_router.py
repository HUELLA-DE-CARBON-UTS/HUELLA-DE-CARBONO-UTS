from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.correo import get_servicio_correo
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.usuario import RegistroUsuarioEntrada
from app.services.use_cases.consultar_usuarios import ConsultarUsuarios
from app.services.use_cases.registrar_usuario import MENSAJE_503 as MSG_FUN01, RegistrarUsuario

router = APIRouter(prefix="/api/v1", tags=["MOD-01 Gestión de Usuarios"])
COMUNES = {401: {"description": "No hay una sesión vigente"}}


@router.post(
    "/usuarios",
    summary="HU-01 Registrar un usuario con su rol y sede inicial",
    description="Registra al colaborador en estado «active», crea sus credenciales con el rol inicial (IC-12) "
                "y las envía a su correo (API-EXT-04). La sede se valida con IC-11. Si el correo no sale, el "
                "usuario queda creado y data.credentialsSent = false. Requiere el permiso FUN-01 (IC-01).",
    response_model=RespuestaEstandar, status_code=201, openapi_extra=ruta("FUN-01", MSG_FUN01),
    responses={
        201: ejemplo(201, "Usuario registrado correctamente", {
            "userId": "USR-0027", "document": "1098765432", "fullName": "Laura Patricia Rueda Gómez",
            "email": "lrueda@empresa-transportadora.co", "role": "Coordinador de operaciones",
            "site": "Bucaramanga", "status": "active", "credentialsSent": True}, None, "FUN-01"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-01"},
        409: ejemplo(409, "Ya existe un usuario con el documento o el correo indicado", None,
                     [{"field": "document", "detail": "El documento 1098765432 ya está registrado"}], "FUN-01"),
        422: ejemplo(422, "La sede o el rol indicados no están disponibles", None,
                     [{"field": "site", "detail": "La sede Cúcuta se encuentra inactiva"}], "FUN-01"),
        503: {"description": MSG_FUN01},
    },
)
def registrar_usuario(
    entrada: RegistroUsuarioEntrada = Body(...),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-01", "No tiene permiso para registrar usuarios")),
    db: Session = Depends(get_db),
    correo=Depends(get_servicio_correo),
):
    datos, enviadas = RegistrarUsuario(db, correo).ejecutar(
        entrada.document, entrada.fullName, entrada.email, entrada.phone, entrada.role, entrada.site,
        sesion.documento)
    mensaje = "Usuario registrado correctamente" if enviadas else \
        "Usuario registrado correctamente, pero no fue posible enviar las credenciales al correo"
    return responder(201, mensaje, datos, funcionalidad="FUN-01")


@router.get(
    "/usuarios",
    summary="HU-02 Buscar usuarios por documento, nombre, sede o estado",
    description="Aplica al mismo tiempo todos los criterios enviados (se exige al menos uno) y retorna documento, "
                "nombres, rol (IC-20), sede (IC-11) y estado, sin credenciales. Requiere el permiso FUN-02 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-02", "No fue posible consultar los usuarios"),
    responses={
        200: ejemplo(200, "Consulta de usuarios exitosa", [
            {"document": "1098765432", "fullName": "Laura Patricia Rueda Gómez", "role": "Coordinador de operaciones",
             "site": "Bucaramanga", "status": "active"}], None, "FUN-02"),
        400: ejemplo(400, "Debe indicar al menos un criterio de búsqueda", None,
                     [{"field": "criteria", "detail": "No se recibió documento, nombre, sede ni estado"}], "FUN-02"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-02"},
        404: ejemplo(404, "Sin resultados", None,
                     [{"field": "criteria", "detail": "No hay usuarios que cumplan todos los criterios"}], "FUN-02"),
        422: {"description": 'El estado debe ser "active" o "inactive"'},
        503: {"description": "No fue posible consultar los usuarios"},
    },
)
def consultar_usuarios(
    document: str | None = Query(None), name: str | None = Query(None),
    site: str | None = Query(None, description="Nombre o identificador de la sede"),
    status: str | None = Query(None, description='"active" o "inactive"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-02", "No tiene permiso para consultar usuarios")),
    db: Session = Depends(get_db),
):
    datos = ConsultarUsuarios(db).ejecutar(document, name, site, status)
    return responder(200, "Consulta de usuarios exitosa", datos, funcionalidad="FUN-02")
