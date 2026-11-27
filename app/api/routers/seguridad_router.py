from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario, sesion_del_token
from app.api.dependencies.correo import get_servicio_correo
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.seguridad import (
    CambioRolEntrada, ConfiguracionRolEntrada, InactivacionRolEntrada, IngresoEntrada, RestablecimientoEntrada)
from app.domain.entities.sesion import Sesion
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.services.use_cases.cerrar_sesion import CerrarSesion
from app.services.use_cases.configurar_rol import ConfigurarRol
from app.services.use_cases.consultar_bitacora import ConsultarBitacora
from app.services.use_cases.gestion_roles import CambiarRolUsuario, ConsultarRoles, ConsultarUsuariosDeRol, InactivarRol
from app.services.use_cases.iniciar_sesion import IniciarSesion
from app.services.use_cases.restablecer_contrasena import RestablecerContrasena
from app.services.mappers import api

router = APIRouter(prefix="/api/v1", tags=["MOD-02 Gestión de Seguridad"])

ID_ROL = Path(..., description="Identificador del rol, por ejemplo ROL-04")
SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


@router.post(
    "/auth/sesiones",
    summary="HU-06 Ingresar al sistema y crear la sesión",
    description="Valida usuario (correo o documento) y contraseña, verifica que el usuario esté activo (IC-14) y "
                "crea la sesión. El token para las demás solicitudes llega en la cabecera **X-Token-Sesion** y se "
                "envía como `Authorization: Bearer <token>`. Si la credencial es temporal, "
                "requiereCambioContrasena = true y la sesión no puede ejecutar operaciones. Cada ingreso e intento "
                "fallido queda en la bitácora.",
    response_model=RespuestaEstandar, status_code=201, openapi_extra=ruta("FUN-06", "No fue posible iniciar la sesión"),
    responses={
        201: {**ejemplo(201, "Ingreso exitoso", {
            "idSesion": "SES-8F21A7", "usuario": "1098765432", "rol": "Coordinador de operaciones",
            "sede": "Bucaramanga", "requiereCambioContrasena": False}, None, "FUN-06"),
            "headers": {"X-Token-Sesion": {"description": "Token de la sesión", "schema": {"type": "string"}}}},
        401: ejemplo(401, "Usuario o contraseña incorrectos", None,
                     [{"campo": "credenciales", "detalle": "Las credenciales no coinciden"}], "FUN-06"),
        403: ejemplo(403, "El usuario no puede ingresar al sistema", None,
                     [{"campo": "usuario", "detalle": "El usuario se encuentra inactivo"}], "FUN-06"),
        422: {"description": "Usuario o contraseña vacíos"},
        503: {"description": "No fue posible iniciar la sesión"},
    },
)
def iniciar_sesion(entrada: IngresoEntrada | None = Body(None), db: Session = Depends(get_db)):
    entrada = entrada or IngresoEntrada()
    datos, token = IniciarSesion(db).ejecutar(entrada.usuario, entrada.contrasena)
    return responder(201, "Ingreso exitoso", datos, funcionalidad="FUN-06", headers={"X-Token-Sesion": token})


@router.delete(
    "/auth/sesiones/{idSesion}",
    summary="HU-08 Cerrar la sesión activa",
    description="Marca la sesión como finalizada y registra la hora de salida en la bitácora. Se envía el token "
                "de la misma sesión que se cierra.",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-08", "No fue posible cerrar la sesión"),
    responses={
        200: ejemplo(200, "Sesión finalizada correctamente",
                     {"idSesion": "SES-8F21A7", "fechaSalida": "2026-11-03T18:02:00-05:00"}, None, "FUN-08"),
        400: ejemplo(400, "El identificador de la sesión no es válido", None,
                     [{"campo": "idSesion", "detalle": "Debe tener el formato SES-XXXXXX"}], "FUN-08"),
        **SIN_SESION,
        403: {"description": "El token enviado pertenece a otra sesión"},
        404: ejemplo(404, "Sesión no encontrada", None,
                     [{"campo": "idSesion", "detalle": "La sesión SES-8F21A7 ya fue finalizada"}], "FUN-08"),
        503: {"description": "No fue posible cerrar la sesión"},
    },
)
def cerrar_sesion(
    idSesion: str = Path(..., description="Identificador de la sesión, formato SES-XXXXXX"),
    sesion: Sesion = Depends(sesion_del_token),
    db: Session = Depends(get_db),
):
    datos = CerrarSesion(db).ejecutar(idSesion, sesion)
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
            "documento": "91234567", "correoDestino": "j***n@empresa-transportadora.co", "sesionesCerradas": 2,
            "credencialTemporalEnviada": True}, None, "FUN-09"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-09"},
        404: ejemplo(404, "Usuario no encontrado", None,
                     [{"campo": "documento", "detalle": "No existe un usuario activo con el documento 91234567"}], "FUN-09"),
        422: {"description": "No se indicó documento ni correo"},
        503: ejemplo(503, "No fue posible enviar la credencial temporal", None,
                     [{"campo": "correo", "detalle": "El servicio de correo (API-EXT-04) no respondió"}], "FUN-09"),
    },
)
def restablecer_contrasena(
    entrada: RestablecimientoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-09", "No tiene permiso para restablecer contraseñas")),
    db: Session = Depends(get_db),
    correo=Depends(get_servicio_correo),
):
    entrada = entrada or RestablecimientoEntrada()
    datos = RestablecerContrasena(db, correo).ejecutar(entrada.documento, entrada.correo, sesion.documento)
    return responder(201, "Contraseña restablecida. La credencial temporal fue enviada al correo registrado", datos,
                     funcionalidad="FUN-09")


@router.get(
    "/auth/bitacora",
    summary="HU-10 Consultar la bitácora de accesos por rango de fechas",
    description="Retorna ingresos, intentos fallidos, operaciones rechazadas y salidas del rango, del más reciente "
                "al más antiguo. Filtros opcionales: usuario (documento) y tipoEvento (ingreso, intento_fallido, "
                "operacion_rechazada o salida). Requiere el permiso FUN-10 (IC-01).",
    response_model=RespuestaEstandar,
    openapi_extra=ruta("FUN-10", "No fue posible consultar la bitácora de accesos"),
    responses={
        200: ejemplo(200, "Consulta de bitácora exitosa", [
            {"usuario": "1098765432", "tipoEvento": "operacion_rechazada", "operacion": "FUN-11",
             "fecha": "2026-11-02T16:40:00-05:00"}], None, "FUN-10"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-10"},
        404: ejemplo(404, "Sin registros en el periodo", None,
                     [{"campo": "fechaInicial", "detalle": "No hay eventos entre 2026-10-01 y 2026-10-02"}], "FUN-10"),
        422: ejemplo(422, "El rango de fechas no es válido", None, [
            {"campo": "fechaInicial", "detalle": "La fecha inicial no puede ser posterior a la fecha final"}], "FUN-10"),
        503: {"description": "No fue posible consultar la bitácora de accesos"},
    },
)
def consultar_bitacora(
    fechaInicial: str | None = Query(None, description="YYYY-MM-DD"),
    fechaFinal: str | None = Query(None, description="YYYY-MM-DD"),
    usuario: str | None = Query(None, description="Documento del usuario"),
    tipoEvento: str | None = Query(None, description="ingreso, intento_fallido, operacion_rechazada o salida"),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-10", "No tiene permiso para consultar la bitácora de accesos")),
    db: Session = Depends(get_db),
):
    datos = ConsultarBitacora(db).ejecutar(fechaInicial, fechaFinal, usuario, tipoEvento)
    return responder(200, "Consulta de bitácora exitosa", datos, funcionalidad="FUN-10")


@router.put(
    "/roles/asignaciones/{documento}",
    summary="HU-12 Cambiar el rol asignado a un usuario activo",
    description="Reemplaza el rol del usuario por otro rol activo. Los nuevos permisos aplican desde su siguiente "
                "operación. Requiere el permiso FUN-12 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-12", CambiarRolUsuario.MENSAJE_503),
    responses={
        200: ejemplo(200, "Rol actualizado correctamente", {
            "documento": "91234567", "rolAnterior": "Coordinador de operaciones", "rolNuevo": "Analista ambiental",
            "aplicaDesde": "siguiente operación"}, None, "FUN-12"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-12"},
        404: {"description": "Usuario no encontrado"},
        409: ejemplo(409, "El usuario ya tiene asignado ese rol", None,
                     [{"campo": "rol", "detalle": "El usuario 91234567 ya tiene el rol Analista ambiental"}], "FUN-12"),
        422: ejemplo(422, "El rol indicado no está disponible", None,
                     [{"campo": "rol", "detalle": "El rol Auditor se encuentra inactivo"}], "FUN-12"),
        503: {"description": CambiarRolUsuario.MENSAJE_503},
    },
)
def cambiar_rol_usuario(
    documento: str = Path(..., description="Documento del usuario"),
    entrada: CambioRolEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-12", "No tiene permiso para cambiar el rol de los usuarios")),
    db: Session = Depends(get_db),
):
    entrada = entrada or CambioRolEntrada()
    datos = CambiarRolUsuario(db).ejecutar(documento, entrada.rol, sesion.documento)
    return responder(200, "Rol actualizado correctamente", datos, funcionalidad="FUN-12")


@router.get(
    "/roles",
    summary="HU-13 Consultar los roles con sus permisos y su número de usuarios",
    description="Retorna cada rol con su estado, sus permisos y su número de usuarios activos (IC-14). El filtro "
                "por estado es opcional. Requiere el permiso FUN-13 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-13", ConsultarRoles.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de roles exitosa", [
            {"idRol": "ROL-01", "nombre": "Administrador", "estado": "activo",
             "permisos": ["FUN-01", "FUN-02", "FUN-11", "FUN-16"], "usuariosActivos": 2}], None, "FUN-13"),
        **SIN_SESION,
        403: ejemplo(403, "No tiene permiso para consultar los roles", None, [
            {"campo": "sesion", "detalle": "El rol Coordinador de operaciones no tiene autorizada la operación FUN-13"}],
            "FUN-13"),
        404: ejemplo(404, "Sin resultados", None, [{"campo": "estado", "detalle": "No hay roles en estado inactivo"}],
                     "FUN-13"),
        422: {"description": 'El estado debe ser "activo" o "inactivo"'},
        503: {"description": ConsultarRoles.MENSAJE_503},
    },
)
def consultar_roles(
    estado: str | None = Query(None, description='"activo" o "inactivo"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-13", "No tiene permiso para consultar los roles")),
    db: Session = Depends(get_db),
):
    datos = ConsultarRoles(db).ejecutar(estado)
    return responder(200, "Consulta de roles exitosa", datos, funcionalidad="FUN-13")


@router.put(
    "/roles/{nombreRol}",
    summary="HU-11 Crear un rol o reemplazar sus permisos",
    description="Crea el rol con estado «activo» y la lista de operaciones autorizadas o, si el rol ya existe, "
                "reemplaza completo su conjunto de permisos. Requiere el permiso FUN-11 (IC-01). "
                "Responde 201 si el rol se creó y 200 si se actualizó.",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-11", "No fue posible guardar la configuración del rol"),
    responses={
        200: {"description": "Permisos del rol reemplazados"},
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-11"},
        422: ejemplo(422, "La configuración del rol no es válida", None,
                     [{"campo": "permisos", "detalle": "La operación FUN-99 no existe en el sistema"}], "FUN-11"),
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
        "estado": api.estado(rol.estado), "permisos": rol.permisos, "accion": api.accion(resultado.accion),
    }
    codigo = 201 if resultado.accion == "creado" else 200
    return responder(codigo, "Rol configurado correctamente", datos, funcionalidad="FUN-11")


@router.patch(
    "/roles/{idRol}/estado",
    summary="HU-14 Inactivar un rol que ningún usuario activo utiliza",
    description="Cambia el rol a «inactivo» conservando sus permisos. Si hay usuarios activos con el rol, se "
                "rechaza e informa cuántos son (IC-14). Requiere el permiso FUN-14 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-14", InactivarRol.MENSAJE_503),
    responses={
        200: ejemplo(200, "Rol inactivado correctamente", {
            "idRol": "ROL-06", "nombre": "Auxiliar de despacho", "estado": "inactivo",
            "motivo": "El cargo se eliminó de la estructura de la empresa"}, None, "FUN-14"),
        400: {"description": "El identificador no tiene el formato ROL-XX"},
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-14"},
        404: ejemplo(404, "Rol no encontrado", None,
                     [{"campo": "idRol", "detalle": "No existe un rol activo con el identificador ROL-99"}], "FUN-14"),
        409: ejemplo(409, "El rol tiene usuarios activos asignados", None,
                     [{"campo": "idRol", "detalle": "El rol ROL-03 tiene 4 usuarios activos"}], "FUN-14"),
        422: {"description": "Motivo vacío"},
        503: {"description": InactivarRol.MENSAJE_503},
    },
)
def inactivar_rol(
    idRol: str = ID_ROL,
    entrada: InactivacionRolEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-14", "No tiene permiso para inactivar roles")),
    db: Session = Depends(get_db),
):
    entrada = entrada or InactivacionRolEntrada()
    datos = InactivarRol(db).ejecutar(idRol, entrada.motivo, sesion.documento)
    return responder(200, "Rol inactivado correctamente", datos, funcionalidad="FUN-14")


@router.get(
    "/roles/{idRol}/usuarios",
    summary="HU-15 Consultar los usuarios que tienen asignado un rol",
    description="Retorna los usuarios activos e inactivos con el rol, con su sede y su estado (IC-14). "
                "Requiere el permiso FUN-15 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-15", ConsultarUsuariosDeRol.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de usuarios del rol exitosa", [
            {"documento": "1098765432", "nombres": "Laura Patricia Rueda Gómez", "sede": "Bucaramanga",
             "estado": "activo"}], None, "FUN-15"),
        400: ejemplo(400, "El identificador del rol no es válido", None,
                     [{"campo": "idRol", "detalle": "Debe tener el formato ROL-XX"}], "FUN-15"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-15"},
        404: ejemplo(404, "Rol no encontrado", None,
                     [{"campo": "idRol", "detalle": "No existe un rol con el identificador ROL-99"}], "FUN-15"),
        503: {"description": ConsultarUsuariosDeRol.MENSAJE_503},
    },
)
def consultar_usuarios_de_rol(
    idRol: str = ID_ROL,
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-15", "No tiene permiso para consultar los usuarios de un rol")),
    db: Session = Depends(get_db),
):
    datos = ConsultarUsuariosDeRol(db).ejecutar(idRol)
    return responder(200, "Consulta de usuarios del rol exitosa", datos, funcionalidad="FUN-15")
