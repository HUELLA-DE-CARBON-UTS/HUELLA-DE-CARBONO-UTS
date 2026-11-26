from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.catalogo import TipoVehiculoEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.catalogo_vehiculos import ConsultarTiposVehiculo, RegistrarTipoVehiculo

router = APIRouter(prefix="/api/v1/catalogos", tags=["MOD-03 Parametrización"])

SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


def _sin_permiso(funcionalidad: str, mensaje: str) -> dict:
    return ejemplo(403, mensaje, None, [
        {"field": "session", "detail": f"El rol no tiene autorizada la operación {funcionalidad}"}], funcionalidad)


@router.post(
    "/tipos-vehiculo",
    summary="HU-21 Registrar un tipo de vehículo con su factor de consumo inicial en L/km",
    description="Registra el tipo de vehículo en estado «active» y guarda su factor de consumo en L/km como "
                "vigente desde la fecha indicada. El nombre no puede repetirse y el factor debe ser numérico y "
                "mayor que 0. Requiere el permiso FUN-21 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-21", RegistrarTipoVehiculo.MENSAJE_503),
    responses={
        201: ejemplo(201, "Tipo de vehículo registrado correctamente", {
            "typeId": "TV-03", "name": "Tractocamión", "status": "active", "consumptionFactorLkm": 0.125,
            "validFrom": "2026-11-01"}, None, "FUN-21"),
        **SIN_SESION,
        403: _sin_permiso("FUN-21", "No tiene permiso para registrar tipos de vehículo"),
        409: ejemplo(409, "El tipo de vehículo ya está registrado", None,
                     [{"field": "name", "detail": "Ya existe el tipo Tractocamión"}], "FUN-21"),
        422: ejemplo(422, "El factor de consumo no es válido", None, [
            {"field": "consumptionFactorLkm", "detail": "Debe ser numérico, mayor que 0 y expresado en L/km"}],
            "FUN-21"),
        503: {"description": RegistrarTipoVehiculo.MENSAJE_503},
    },
)
def registrar_tipo_vehiculo(
    entrada: TipoVehiculoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-21", "No tiene permiso para registrar tipos de vehículo")),
    db: Session = Depends(get_db),
):
    entrada = entrada or TipoVehiculoEntrada()
    datos = RegistrarTipoVehiculo(db).ejecutar(entrada.name, entrada.description, entrada.consumptionFactorLkm,
                                               entrada.startDate, sesion.documento)
    return responder(201, "Tipo de vehículo registrado correctamente", datos, funcionalidad="FUN-21")


@router.get(
    "/tipos-vehiculo",
    summary="HU-23 Consultar los tipos de vehículo con su factor de consumo vigente",
    description="Retorna los tipos de vehículo con el factor en L/km vigente en la fecha de consulta. Los tipos "
                "sin factor vigente se señalan con noCurrentFactor = true. El filtro por estado es opcional. "
                "Requiere el permiso FUN-23 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-23", ConsultarTiposVehiculo.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de tipos de vehículo exitosa", [
            {"typeId": "TV-01", "name": "Camión sencillo", "status": "active", "currentFactorLkm": 0.095},
            {"typeId": "TV-04", "name": "Furgón eléctrico", "status": "active", "currentFactorLkm": None,
             "noCurrentFactor": True}], None, "FUN-23"),
        **SIN_SESION,
        403: _sin_permiso("FUN-23", "No tiene permiso para consultar el catálogo"),
        404: ejemplo(404, "Sin resultados", None,
                     [{"field": "status", "detail": "No hay tipos de vehículo inactivos"}], "FUN-23"),
        422: ejemplo(422, "Los criterios de consulta no son válidos", None,
                     [{"field": "status", "detail": 'El estado debe ser "active" o "inactive"'}], "FUN-23"),
        503: {"description": ConsultarTiposVehiculo.MENSAJE_503},
    },
)
def consultar_tipos_vehiculo(
    status: str | None = Query(None, description='"active" o "inactive"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-23", "No tiene permiso para consultar el catálogo")),
    db: Session = Depends(get_db),
):
    datos = ConsultarTiposVehiculo(db).ejecutar(status)
    return responder(200, "Consulta de tipos de vehículo exitosa", datos, funcionalidad="FUN-23")
