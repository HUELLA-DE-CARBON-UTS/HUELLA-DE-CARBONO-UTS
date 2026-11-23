from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario, sesion_del_token
from app.api.dependencies.correo import get_servicio_correo
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.seguridad import ConfiguracionRolEntrada, IngresoEntrada, RestablecimientoEntrada
from app.domain.entities.sesion import Sesion
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.services.use_cases.cerrar_sesion import CerrarSesion
from app.services.use_cases.configurar_rol import ConfigurarRol
from app.services.use_cases.iniciar_sesion import IniciarSesion
from app.services.use_cases.restablecer_contrasena import RestablecerContrasena
from app.services.mappers import api

router = APIRouter(prefix="/api/v1", tags=["MOD-02 Gestión de Seguridad"])
SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


@router.post(
    "/auth/sesiones",
    summary="HU-06 Ingresar al sistema y crear la sesión",
    description="Valida usuario (correo o documento) y contraseña, verifica que el usuario esté activo (IC-14) y "
                "crea la sesión. El token para las demás solicitudes llega en la cabecera **X-Token-Sesion** y se "
                "envía como `Authorization: Bearer <token>`. Si la credencial es temporal, "
                "passwordChangeRequired = true y la sesión no puede ejecutar operaciones. Cada ingreso e intento "
                "fallido queda en la bitácora.",
    response_model=RespuestaEstandar, status_code=201, openapi_extra=ruta("FUN-06", "No fue posible iniciar la sesión"),
    responses={
        201: {**ejemplo(201, "Ingreso exitoso", {
            "sessionId": "SES-8F21A7", "user": "1098765432", "role": "Coordinador de operaciones",
            "site": "Bucaramanga", "passwordChangeRequired": False}, None, "FUN-06"),
            "headers": {"X-Token-Sesion": {"description": "Token de la sesión", "schema": {"type": "string"}}}},
        401: ejemplo(401, "Usuario o contraseña incorrectos", None,
                     [{"field": "credentials", "detail": "Las credenciales no coinciden"}], "FUN-06"),
        403: ejemplo(403, "El usuario no puede ingresar al sistema", None,
                     [{"field": "username", "detail": "El usuario se encuentra inactivo"}], "FUN-06"),
        422: {"description": "Usuario o contraseña vacíos"},
        503: {"description": "No fue posible iniciar la sesión"},
    },
)
def iniciar_sesion(entrada: IngresoEntrada | None = Body(None), db: Session = Depends(get_db)):
    entrada = entrada or IngresoEntrada()
    datos, token = IniciarSesion(db).ejecutar(entrada.username, entrada.password)
    return responder(201, "Ingreso exitoso", datos, funcionalidad="FUN-06", headers={"X-Token-Sesion": token})


@router.delete(
    "/auth/sesiones/{sessionId}",
    summary="HU-08 Cerrar la sesión activa",
    description="Marca la sesión como finalizada y registra la hora de salida en la bitácora. Se envía el token "
                "de la misma sesión que se cierra.",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-08", "No fue posible cerrar la sesión"),
    responses={
        200: ejemplo(200, "Sesión finalizada correctamente",
                     {"sessionId": "SES-8F21A7", "logoutDate": "2026-11-03T18:02:00-05:00"}, None, "FUN-08"),
        400: ejemplo(400, "El identificador de la sesión no es válido", None,
                     [{"field": "sessionId", "detail": "Debe tener el formato SES-XXXXXX"}], "FUN-08"),
        **SIN_SESION,
        403: {"description": "El token enviado pertenece a otra sesión"},
        404: ejemplo(404, "Sesión no encontrada", None,
                     [{"field": "sessionId", "detail": "La sesión SES-8F21A7 ya fue finalizada"}], "FUN-08"),
        503: {"description": "No fue posible cerrar la sesión"},
    },
)
def cerrar_sesion(
    sessionId: str = Path(..., description="Identificador de la sesión, formato SES-XXXXXX"),
    sesion: Sesion = Depends(sesion_del_token),
    db: Session = Depends(get_db),
):
    datos = CerrarSesion(db).ejecutar(sessionId, sesion)
    return responder(200, "Sesión finalizada correctamente", datos, funcionalidad="FUN-08")


@router.post(
    "/auth/restablecimientos",
    summary="HU-09 Restablecer la contraseña con una credencial temporal",
    description="Genera una credencial temporal de un solo uso que reemplaza la anterior, cierra las sesiones "
                "abiertas del usuario (IC-13) y la envía a su correo (API-EXT-04). La respuesta nunca incluye la "
                "credencial. Requiere el permiso FUN-09 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-09", "No fue posible restablecer la contraseña"),
    responses={
        201: ejemplo(201, "Contraseña restablecida. La credencial temporal fue enviada al correo registrado", {
            "document": "91234567", "destinationEmail": "j***n@empresa-transportadora.co", "closedSessions": 2,
            "temporaryCredentialSent": True}, None, "FUN-09"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-09"},
        404: ejemplo(404, "Usuario no encontrado", None,
                     [{"field": "document", "detail": "No existe un usuario activo con el documento 91234567"}], "FUN-09"),
        422: {"description": "No se indicó documento ni correo"},
        503: ejemplo(503, "No fue posible enviar la credencial temporal", None,
                     [{"field": "email", "detail": "El servicio de correo (API-EXT-04) no respondió"}], "FUN-09"),
    },
)
def restablecer_contrasena(
    entrada: RestablecimientoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-09", "No tiene permiso para restablecer contraseñas")),
    db: Session = Depends(get_db),
    correo=Depends(get_servicio_correo),
):
    entrada = entrada or RestablecimientoEntrada()
    datos = RestablecerContrasena(db, correo).ejecutar(entrada.document, entrada.email, sesion.documento)
    return responder(201, "Contraseña restablecida. La credencial temporal fue enviada al correo registrado", datos,
                     funcionalidad="FUN-09")


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
