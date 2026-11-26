from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.catalogo import TipoVehiculoEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.catalogo_vehiculos import RegistrarTipoVehiculo

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
