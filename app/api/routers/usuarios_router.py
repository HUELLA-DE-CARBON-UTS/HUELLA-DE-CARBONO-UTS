from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.correo import get_servicio_correo
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.usuario import CambioEstadoEntrada, ContactoEntrada, RegistroUsuarioEntrada, TrasladoEntrada
from app.services.use_cases.actualizar_contacto import ActualizarContacto
from app.services.use_cases.cambiar_estado_usuario import CambiarEstadoUsuario
from app.services.use_cases.consultar_usuarios import ConsultarUsuarios
from app.services.use_cases.registrar_usuario import MENSAJE_503 as MSG_FUN01, RegistrarUsuario
from app.services.use_cases.reubicar_usuario import ReubicarUsuario

router = APIRouter(prefix="/api/v1", tags=["MOD-01 Gestión de Usuarios"])

DOCUMENTO = Path(..., description="Documento del usuario")
COMUNES = {401: {"description": "No hay una sesión vigente"}}


@router.post(
    "/usuarios",
    summary="HU-01 Registrar un usuario con su rol y sede inicial",
    description="Registra al colaborador en estado «activo», crea sus credenciales con el rol inicial (IC-12) "
                "y las envía a su correo (API-EXT-04). La sede se valida con IC-11. Si el correo no sale, el "
                "usuario queda creado y data.credencialesEnviadas = false. Requiere el permiso FUN-01 (IC-01).",
    response_model=RespuestaEstandar, status_code=201, openapi_extra=ruta("FUN-01", MSG_FUN01),
    responses={
        201: ejemplo(201, "Usuario registrado correctamente", {
            "idUsuario": "USR-0027", "documento": "1098765432", "nombres": "Laura Patricia Rueda Gómez",
            "correo": "lrueda@empresa-transportadora.co", "rol": "Coordinador de operaciones",
            "sede": "Bucaramanga", "estado": "activo", "credencialesEnviadas": True}, None, "FUN-01"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-01"},
        409: ejemplo(409, "Ya existe un usuario con el documento o el correo indicado", None,
                     [{"campo": "documento", "detalle": "El documento 1098765432 ya está registrado"}], "FUN-01"),
        422: ejemplo(422, "La sede o el rol indicados no están disponibles", None,
                     [{"campo": "sede", "detalle": "La sede Cúcuta se encuentra inactiva"}], "FUN-01"),
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
        entrada.documento, entrada.nombres, entrada.correo, entrada.telefono, entrada.rol, entrada.sede,
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
            {"documento": "1098765432", "nombres": "Laura Patricia Rueda Gómez", "rol": "Coordinador de operaciones",
             "sede": "Bucaramanga", "estado": "activo"}], None, "FUN-02"),
        400: ejemplo(400, "Debe indicar al menos un criterio de búsqueda", None,
                     [{"campo": "criterios", "detalle": "No se recibió documento, nombre, sede ni estado"}], "FUN-02"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-02"},
        404: ejemplo(404, "Sin resultados", None,
                     [{"campo": "criterios", "detalle": "No hay usuarios que cumplan todos los criterios"}], "FUN-02"),
        422: {"description": 'El estado debe ser "activo" o "inactivo"'},
        503: {"description": "No fue posible consultar los usuarios"},
    },
)
def consultar_usuarios(
    documento: str | None = Query(None), nombre: str | None = Query(None),
    sede: str | None = Query(None, description="Nombre o identificador de la sede"),
    estado: str | None = Query(None, description='"activo" o "inactivo"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-02", "No tiene permiso para consultar usuarios")),
    db: Session = Depends(get_db),
):
    datos = ConsultarUsuarios(db).ejecutar(documento, nombre, sede, estado)
    return responder(200, "Consulta de usuarios exitosa", datos, funcionalidad="FUN-02")


@router.patch(
    "/usuarios/{documento}/estado",
    summary="HU-03 Cambiar el estado de un usuario entre activo e inactivo",
    description="Cambia el estado con su motivo. Al inactivar, cierra las sesiones abiertas del usuario (IC-13). "
                "El administrador no puede inactivarse a sí mismo. Requiere el permiso FUN-03 (IC-01).",
    response_model=RespuestaEstandar,
    openapi_extra=ruta("FUN-03", "No fue posible actualizar el estado del usuario"),
    responses={
        200: ejemplo(200, "Estado del usuario actualizado correctamente", {
            "documento": "91234567", "estadoAnterior": "activo", "estadoNuevo": "inactivo",
            "motivo": "Retiro voluntario de la empresa", "sesionesCerradas": 1}, None, "FUN-03"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-03"},
        404: {"description": "Usuario no encontrado"},
        409: ejemplo(409, "No es posible cambiar el estado del usuario", None,
                     [{"campo": "documento", "detalle": "El administrador no puede inactivarse a sí mismo"}], "FUN-03"),
        422: {"description": "Estado no válido o motivo vacío"},
        503: {"description": "No fue posible actualizar el estado del usuario"},
    },
)
def cambiar_estado_usuario(
    documento: str = DOCUMENTO,
    entrada: CambioEstadoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-03", "No tiene permiso para cambiar el estado de los usuarios")),
    db: Session = Depends(get_db),
):
    entrada = entrada or CambioEstadoEntrada()
    datos = CambiarEstadoUsuario(db).ejecutar(documento, entrada.estado, entrada.motivo, sesion.documento)
    return responder(200, "Estado del usuario actualizado correctamente", datos, funcionalidad="FUN-03")


@router.patch(
    "/usuarios/{documento}/sede",
    summary="HU-04 Trasladar un usuario a otra sede activa",
    description="Reubica a un usuario activo en otra sede activa y distinta de la actual (IC-11) y registra el "
                "traslado con sede de origen, sede de destino, fecha y responsable. Requiere el permiso FUN-04 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-04", "No fue posible reubicar al usuario"),
    responses={
        200: ejemplo(200, "Usuario reubicado correctamente", {
            "documento": "1098765432", "sedeOrigen": "Bucaramanga", "sedeDestino": "Cúcuta",
            "fechaTraslado": "2026-11-03"}, None, "FUN-04"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-04"},
        404: {"description": "Usuario no encontrado"},
        422: ejemplo(422, "La sede de destino no es válida", None,
                     [{"campo": "sedeDestino", "detalle": "La sede de destino es la misma sede actual del usuario"}],
                     "FUN-04"),
        503: {"description": "No fue posible reubicar al usuario"},
    },
)
def reubicar_usuario(
    documento: str = DOCUMENTO,
    entrada: TrasladoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-04", "No tiene permiso para reubicar usuarios")),
    db: Session = Depends(get_db),
):
    entrada = entrada or TrasladoEntrada()
    datos = ReubicarUsuario(db).ejecutar(documento, entrada.sedeDestino, sesion.documento)
    return responder(200, "Usuario reubicado correctamente", datos, funcionalidad="FUN-04")


@router.patch(
    "/usuarios/{documento}/contacto",
    summary="HU-05 Modificar el correo y el teléfono de un usuario",
    description="Actualiza el correo y/o el teléfono de un usuario activo, conservando documento, rol y sede, y "
                "registra los valores anteriores. Requiere el permiso FUN-05 (IC-01).",
    response_model=RespuestaEstandar,
    openapi_extra=ruta("FUN-05", "No fue posible actualizar los datos de contacto"),
    responses={
        200: ejemplo(200, "Datos de contacto actualizados correctamente", {
            "documento": "1098765432", "correoAnterior": "lrueda@empresa-transportadora.co",
            "correoNuevo": "laura.rueda@empresa-transportadora.co", "telefono": "3157894512"}, None, "FUN-05"),
        **COMUNES,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-05"},
        404: {"description": "Usuario no encontrado"},
        409: ejemplo(409, "El correo ya pertenece a otro usuario", None, [
            {"campo": "correo", "detalle": "El correo jpabon@empresa-transportadora.co está asignado al usuario 91234567"}],
            "FUN-05"),
        422: {"description": "Correo o teléfono con formato no válido"},
        503: {"description": "No fue posible actualizar los datos de contacto"},
    },
)
def actualizar_contacto(
    documento: str = DOCUMENTO,
    entrada: ContactoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-05", "No tiene permiso para actualizar los datos de contacto")),
    db: Session = Depends(get_db),
):
    entrada = entrada or ContactoEntrada()
    datos = ActualizarContacto(db).ejecutar(documento, entrada.correo, entrada.telefono, sesion.documento)
    return responder(200, "Datos de contacto actualizados correctamente", datos, funcionalidad="FUN-05")
