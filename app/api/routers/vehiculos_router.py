from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.schemas.vehiculo import VehiculoEntrada
from app.services.use_cases.flota_vehiculos import ConsultarVehiculos, RegistrarVehiculo

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


@router.get(
    "",
    summary="HU-34 Buscar vehículos por placa, tipo, sede o estado",
    description="Aplica al mismo tiempo todos los criterios enviados (se exige al menos uno) y retorna placa, tipo, "
                "combustible, sede y estado de cada vehículo. Requiere el permiso FUN-34 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-34", ConsultarVehiculos.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de vehículos exitosa", [
            {"placa": "TTK-482", "tipo": "Tractocamión", "combustible": "Diésel", "sede": "Bucaramanga",
             "estado": "disponible"},
            {"placa": "WFN-731", "tipo": "Tractocamión", "combustible": "Diésel", "sede": "Bucaramanga",
             "estado": "disponible"}], None, "FUN-34"),
        400: ejemplo(400, "Debe indicar al menos un criterio de búsqueda", None,
                     [{"campo": "criterios", "detalle": "No se recibió placa, tipo, sede ni estado"}], "FUN-34"),
        **SIN_SESION,
        403: _sin_permiso("FUN-34", "No tiene permiso para consultar los vehículos"),
        404: ejemplo(404, "Sin resultados", None,
                     [{"campo": "criterios", "detalle": "No hay vehículos que cumplan los criterios"}], "FUN-34"),
        422: ejemplo(422, "Los criterios de búsqueda no son válidos", None, [
            {"campo": "estado", "detalle": 'El estado debe ser "disponible", "asignado" o "fuera de servicio"'}],
            "FUN-34"),
        503: {"description": ConsultarVehiculos.MENSAJE_503},
    },
)
def consultar_vehiculos(
    placa: str | None = Query(None, description="Placa completa o parte de ella"),
    tipo: str | None = Query(None, description="Nombre o identificador (TV-XX) del tipo de vehículo"),
    sede: str | None = Query(None, description="Nombre o identificador (SED-XX) de la sede"),
    estado: str | None = Query(None, description='"disponible", "asignado" o "fuera de servicio"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-34", "No tiene permiso para consultar los vehículos")),
    db: Session = Depends(get_db),
):
    datos = ConsultarVehiculos(db).ejecutar(placa, tipo, sede, estado)
    return responder(200, "Consulta de vehículos exitosa", datos, funcionalidad="FUN-34")
