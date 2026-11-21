from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.seguridad import ConfiguracionRolEntrada, IngresoEntrada
from app.domain.entities.sesion import Sesion
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.services.use_cases.configurar_rol import ConfigurarRol
from app.services.use_cases.iniciar_sesion import IniciarSesion
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
