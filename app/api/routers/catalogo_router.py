from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.catalogo import FactorConsumoEntrada, TipoVehiculoEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.catalogo_vehiculos import (
    ActualizarFactorConsumo, ConsultarHistoricoConsumo, ConsultarTiposVehiculo, RegistrarTipoVehiculo)

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


@router.post(
    "/tipos-vehiculo/{typeId}/factores-consumo",
    summary="HU-22 Actualizar el factor de consumo de un tipo de vehículo desde una fecha",
    description="Cierra el factor vigente el día anterior a la nueva fecha y guarda el nuevo factor como vigente. "
                "Los recorridos ya calculados conservan el factor con que se calcularon. El tipo debe existir y "
                "estar activo. Requiere el permiso FUN-22 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-22", ActualizarFactorConsumo.MENSAJE_503),
    responses={
        201: ejemplo(201, "Factor de consumo actualizado correctamente", {
            "typeId": "TV-03", "previousFactor": {"valueLkm": 0.125, "validTo": "2026-12-31"},
            "newFactor": {"valueLkm": 0.118, "validFrom": "2027-01-01"}}, None, "FUN-22"),
        **SIN_SESION,
        403: _sin_permiso("FUN-22", "No tiene permiso para actualizar el factor de consumo"),
        404: ejemplo(404, "Tipo de vehículo no encontrado", None,
                     [{"field": "typeId", "detail": "No existe un tipo activo con el identificador TV-09"}],
                     "FUN-22"),
        422: ejemplo(422, "La fecha del nuevo factor no es válida", None, [
            {"field": "startDate", "detail": "No puede ser anterior al inicio del factor vigente (2026-11-01)"}],
            "FUN-22"),
        503: {"description": ActualizarFactorConsumo.MENSAJE_503},
    },
)
def actualizar_factor_consumo(
    typeId: str = Path(..., description="Identificador del tipo de vehículo, por ejemplo TV-03"),
    entrada: FactorConsumoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-22", "No tiene permiso para actualizar el factor de consumo")),
    db: Session = Depends(get_db),
):
    entrada = entrada or FactorConsumoEntrada()
    datos = ActualizarFactorConsumo(db).ejecutar(typeId, entrada.consumptionFactorLkm, entrada.startDate,
                                                 sesion.documento)
    return responder(201, "Factor de consumo actualizado correctamente", datos, funcionalidad="FUN-22")


@router.get(
    "/tipos-vehiculo/{typeId}/factores-consumo",
    summary="HU-24 Consultar el histórico de factores de consumo de un tipo de vehículo",
    description="Retorna todos los factores del tipo con sus fechas de inicio y fin y su responsable, del más "
                "reciente al más antiguo, señalando el vigente con current = true. Requiere el permiso FUN-24 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-24", ConsultarHistoricoConsumo.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta del histórico de factores exitosa", [
            {"valueLkm": 0.118, "validFrom": "2027-01-01", "validTo": None, "registeredBy": "63456789",
             "current": True},
            {"valueLkm": 0.125, "validFrom": "2026-11-01", "validTo": "2026-12-31", "registeredBy": "63456789",
             "current": False}], None, "FUN-24"),
        400: ejemplo(400, "El identificador del tipo de vehículo no es válido", None,
                     [{"field": "typeId", "detail": "Debe tener el formato TV-XX"}], "FUN-24"),
        **SIN_SESION,
        403: _sin_permiso("FUN-24", "No tiene permiso para consultar el histórico"),
        404: ejemplo(404, "Tipo de vehículo no encontrado", None,
                     [{"field": "typeId", "detail": "No existe un tipo con el identificador TV-09"}], "FUN-24"),
        503: {"description": ConsultarHistoricoConsumo.MENSAJE_503},
    },
)
def consultar_historico_consumo(
    typeId: str = Path(..., description="Identificador del tipo de vehículo, por ejemplo TV-03"),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-24", "No tiene permiso para consultar el histórico")),
    db: Session = Depends(get_db),
):
    datos = ConsultarHistoricoConsumo(db).ejecutar(typeId)
    return responder(200, "Consulta del histórico de factores exitosa", datos, funcionalidad="FUN-24")
