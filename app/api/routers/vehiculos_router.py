from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.vehiculo import VehiculoEntrada
from app.services.use_cases.flota_vehiculos import RegistrarVehiculo

router = APIRouter(prefix="/api/v1/vehiculos", tags=["MOD-04 Gestión de Flota"])

SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


def _sin_permiso(funcionalidad: str, mensaje: str) -> dict:
    return ejemplo(403, mensaje, None, [
        {"campo": "sesion", "detalle": f"El rol no tiene autorizada la operación {funcionalidad}"}], funcionalidad)


@router.post(
    "",
    summary="HU-31 Registrar un camión nuevo disponible para operar",
    description="Registra el vehículo en estado «disponible» con su placa, tipo, combustible, capacidad en "
                "toneladas y sede. El tipo debe tener factor de consumo vigente y el combustible factor de emisión "
                "vigente (IC-02), y la sede debe estar activa (IC-11). La placa es única y tiene el formato AAA-000. "
                "Requiere el permiso FUN-31 (IC-01).",
    response_model=RespuestaEstandar, status_code=201, openapi_extra=ruta("FUN-31", RegistrarVehiculo.MENSAJE_503),
    responses={
        201: ejemplo(201, "Vehículo registrado correctamente", {
            "placa": "TTK-482", "tipoVehiculo": "Tractocamión", "combustible": "Diésel", "capacidadT": 34,
            "sede": "Bucaramanga", "estado": "disponible"}, None, "FUN-31"),
        **SIN_SESION,
        403: _sin_permiso("FUN-31", "No tiene permiso para registrar vehículos"),
        409: ejemplo(409, "La placa ya está registrada", None,
                     [{"campo": "placa", "detalle": "Ya existe un vehículo con la placa TTK-482"}], "FUN-31"),
        422: ejemplo(422, "El tipo de vehículo o el combustible no tienen factor vigente", None, [
            {"campo": "tipoVehiculo", "detalle": "El tipo Furgón eléctrico no tiene factor de consumo vigente"}],
            "FUN-31"),
        503: {"description": RegistrarVehiculo.MENSAJE_503},
    },
)
def registrar_vehiculo(
    entrada: VehiculoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-31", "No tiene permiso para registrar vehículos")),
    db: Session = Depends(get_db),
):
    entrada = entrada or VehiculoEntrada()
    datos = RegistrarVehiculo(db).ejecutar(entrada.placa, entrada.tipoVehiculo, entrada.combustible, entrada.capacidadT,
                                           entrada.sede, sesion.documento)
    return responder(201, "Vehículo registrado correctamente", datos, funcionalidad="FUN-31")
