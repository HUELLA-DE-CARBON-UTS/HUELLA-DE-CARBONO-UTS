from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.parametrizacion import SedeEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.repositories.adapters.sede_repositorio_sqlalchemy import SedeRepositorioSQLAlchemy
from app.services.use_cases.gestion_sedes import ConsultarSedes
from app.services.use_cases.registrar_sede import RegistrarSede
from app.services.mappers import api

router = APIRouter(prefix="/api/v1", tags=["MOD-03 Parametrización"])

SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


@router.post(
    "/sedes",
    summary="HU-16 Registrar una nueva sede",
    description="Registra una sede con su nombre, ciudad, dirección y responsable. La sede queda en estado "
                "«active» con su fecha de creación. No se permiten dos sedes con el mismo nombre en la misma "
                "ciudad. Requiere el permiso FUN-16 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-16", "No fue posible registrar la sede"),
    responses={
        201: ejemplo(201, "Sede registrada correctamente", {
            "siteId": "SED-05", "name": "Barranquilla", "city": "Barranquilla",
            "address": "Calle 30 # 1-25, zona industrial", "manager": "Carolina Herrera Pérez",
            "status": "active"}, None, "FUN-16"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-16"},
        409: ejemplo(409, "Ya existe una sede con ese nombre en la ciudad", None,
                     [{"field": "name", "detail": "La sede Barranquilla ya está registrada en Barranquilla"}], "FUN-16"),
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
        entrada.name, entrada.city, entrada.address, entrada.manager)
    datos = {
        "siteId": sede.id_sede, "name": sede.nombre, "city": sede.ciudad,
        "address": sede.direccion, "manager": sede.responsable, "status": api.estado(sede.estado),
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
            {"siteId": "SED-01", "name": "Bucaramanga", "city": "Bucaramanga",
             "manager": "Sergio Díaz Mantilla", "status": "active"}], None, "FUN-19"),
        **SIN_SESION,
        403: ejemplo(403, "No tiene permiso para consultar las sedes", None,
                     [{"field": "session", "detail": "El rol no tiene autorizada la operación FUN-19"}], "FUN-19"),
        404: ejemplo(404, "Sin resultados", None, [{"field": "city", "detail": "No hay sedes registradas en Pasto"}],
                     "FUN-19"),
        422: {"description": 'El estado debe ser "active" o "inactive"'},
        503: {"description": ConsultarSedes.MENSAJE_503},
    },
)
def consultar_sedes(
    city: str | None = Query(None),
    status: str | None = Query(None, description='"active" o "inactive"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-19", "No tiene permiso para consultar las sedes")),
    db: Session = Depends(get_db),
):
    datos = ConsultarSedes(db).ejecutar(city, status)
    return responder(200, "Consulta de sedes exitosa", datos, funcionalidad="FUN-19")
