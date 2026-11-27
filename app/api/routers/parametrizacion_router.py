from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.parametrizacion import ActualizacionSedeEntrada, SedeEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.repositories.adapters.sede_repositorio_sqlalchemy import SedeRepositorioSQLAlchemy
from app.services.use_cases.gestion_sedes import ActualizarSede, ConsultarSedes
from app.services.use_cases.registrar_sede import RegistrarSede
from app.services.mappers import api

router = APIRouter(prefix="/api/v1", tags=["MOD-03 Parametrización"])

SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


@router.post(
    "/sedes",
    summary="HU-16 Registrar una nueva sede",
    description="Registra una sede con su nombre, ciudad, dirección y responsable. La sede queda en estado "
                "«activa» con su fecha de creación. No se permiten dos sedes con el mismo nombre en la misma "
                "ciudad. Requiere el permiso FUN-16 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-16", "No fue posible registrar la sede"),
    responses={
        201: ejemplo(201, "Sede registrada correctamente", {
            "idSede": "SED-05", "nombre": "Barranquilla", "ciudad": "Barranquilla",
            "direccion": "Calle 30 # 1-25, zona industrial", "responsable": "Carolina Herrera Pérez",
            "estado": "activa"}, None, "FUN-16"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-16"},
        409: ejemplo(409, "Ya existe una sede con ese nombre en la ciudad", None,
                     [{"campo": "nombre", "detalle": "La sede Barranquilla ya está registrada en Barranquilla"}], "FUN-16"),
        422: {"description": "Falta un campo obligatorio o supera su longitud"},
        503: {"description": "No fue posible registrar la sede"},
    },
)
def registrar_sede(
    entrada: SedeEntrada | None = Body(None),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-16", "No tiene permiso para registrar sedes")),
    db: Session = Depends(get_db),
):
    entrada = entrada or SedeEntrada()
    sede = RegistrarSede(SedeRepositorioSQLAlchemy(db)).ejecutar(
        entrada.nombre, entrada.ciudad, entrada.direccion, entrada.responsable)
    datos = {
        "idSede": sede.id_sede, "nombre": sede.nombre, "ciudad": sede.ciudad,
        "direccion": sede.direccion, "responsable": sede.responsable, "estado": api.estado(sede.estado),
    }
    return responder(201, "Sede registrada correctamente", datos, funcionalidad="FUN-16")


@router.get(
    "/sedes",
    summary="HU-19 Consultar el listado de sedes por ciudad o estado",
    description="Retorna las sedes ordenadas por ciudad y nombre. Los filtros de ciudad y estado son opcionales. "
                "Requiere el permiso FUN-19 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-19", ConsultarSedes.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de sedes exitosa", [
            {"idSede": "SED-01", "nombre": "Bucaramanga", "ciudad": "Bucaramanga",
             "responsable": "Sergio Díaz Mantilla", "estado": "activa"}], None, "FUN-19"),
        **SIN_SESION,
        403: ejemplo(403, "No tiene permiso para consultar las sedes", None,
                     [{"campo": "sesion", "detalle": "El rol no tiene autorizada la operación FUN-19"}], "FUN-19"),
        404: ejemplo(404, "Sin resultados", None, [{"campo": "ciudad", "detalle": "No hay sedes registradas en Pasto"}],
                     "FUN-19"),
        422: {"description": 'El estado debe ser "activa" o "inactiva"'},
        503: {"description": ConsultarSedes.MENSAJE_503},
    },
)
def consultar_sedes(
    ciudad: str | None = Query(None),
    estado: str | None = Query(None, description='"activa" o "inactiva"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-19", "No tiene permiso para consultar las sedes")),
    db: Session = Depends(get_db),
):
    datos = ConsultarSedes(db).ejecutar(ciudad, estado)
    return responder(200, "Consulta de sedes exitosa", datos, funcionalidad="FUN-19")


@router.patch(
    "/sedes/{idSede}",
    summary="HU-17 Actualizar la dirección, ciudad o responsable de una sede",
    description="Modifica solo los campos enviados de una sede activa (nombre, ciudad, dirección o responsable), "
                "sin dejarlos vacíos, y registra los valores anteriores con fecha y responsable. "
                "Requiere el permiso FUN-17 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-17", ActualizarSede.MENSAJE_503),
    responses={
        200: ejemplo(200, "Sede actualizada correctamente", {
            "idSede": "SED-02", "nombre": "Cúcuta", "direccionAnterior": "Av. 7 # 12-40",
            "direccionNueva": "Anillo vial occidental, bodega 14", "responsable": "Mauricio Contreras Ibáñez"},
            None, "FUN-17"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-17"},
        404: ejemplo(404, "Sede no encontrada", None,
                     [{"campo": "idSede", "detalle": "No existe una sede activa con el identificador SED-09"}], "FUN-17"),
        409: ejemplo(409, "Ya existe una sede con ese nombre en la ciudad", None,
                     [{"campo": "nombre", "detalle": "El nombre Bucaramanga ya lo usa otra sede de la ciudad"}], "FUN-17"),
        422: {"description": "Un campo modificado quedó vacío"},
        503: {"description": ActualizarSede.MENSAJE_503},
    },
)
def actualizar_sede(
    idSede: str = Path(..., description="Identificador de la sede, por ejemplo SED-02"),
    entrada: ActualizacionSedeEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-17", "No tiene permiso para actualizar sedes")),
    db: Session = Depends(get_db),
):
    entrada = entrada or ActualizacionSedeEntrada()
    cambios = {"nombre": entrada.nombre, "ciudad": entrada.ciudad, "direccion": entrada.direccion,
               "responsable": entrada.responsable}
    datos = ActualizarSede(db).ejecutar(idSede, cambios, sesion.documento)
    return responder(200, "Sede actualizada correctamente", datos, funcionalidad="FUN-17")
