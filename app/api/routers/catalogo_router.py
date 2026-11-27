from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.catalogo import CombustibleEntrada, FactorConsumoEntrada, FactorEmisionEntrada, TipoVehiculoEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.catalogo_combustibles import (
    ActualizarFactorEmision, ConsultarCombustibles, ConsultarHistoricoEmision, RegistrarCombustible)
from app.services.use_cases.catalogo_vehiculos import (
    ActualizarFactorConsumo, ConsultarHistoricoConsumo, ConsultarTiposVehiculo, RegistrarTipoVehiculo)

router = APIRouter(prefix="/api/v1/catalogos", tags=["MOD-03 Parametrización"])

SIN_SESION = {401: {"description": "No hay una sesión vigente"}}
FUENTE = "Fuente oficial consultada por API-EXT-03 (valor ilustrativo)"


def _sin_permiso(funcionalidad: str, mensaje: str) -> dict:
    return ejemplo(403, mensaje, None, [
        {"campo": "sesion", "detalle": f"El rol no tiene autorizada la operación {funcionalidad}"}], funcionalidad)


@router.post(
    "/tipos-vehiculo",
    summary="HU-21 Registrar un tipo de vehículo con su factor de consumo inicial en L/km",
    description="Registra el tipo de vehículo en estado «activo» y guarda su factor de consumo en L/km como "
                "vigente desde la fecha indicada. El nombre no puede repetirse y el factor debe ser numérico y "
                "mayor que 0. Requiere el permiso FUN-21 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-21", RegistrarTipoVehiculo.MENSAJE_503),
    responses={
        201: ejemplo(201, "Tipo de vehículo registrado correctamente", {
            "idTipo": "TV-03", "nombre": "Tractocamión", "estado": "activo", "factorConsumoLkm": 0.125,
            "vigenteDesde": "2026-11-01"}, None, "FUN-21"),
        **SIN_SESION,
        403: _sin_permiso("FUN-21", "No tiene permiso para registrar tipos de vehículo"),
        409: ejemplo(409, "El tipo de vehículo ya está registrado", None,
                     [{"campo": "nombre", "detalle": "Ya existe el tipo Tractocamión"}], "FUN-21"),
        422: ejemplo(422, "El factor de consumo no es válido", None, [
            {"campo": "factorConsumoLkm", "detalle": "Debe ser numérico, mayor que 0 y expresado en L/km"}],
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
    datos = RegistrarTipoVehiculo(db).ejecutar(entrada.nombre, entrada.descripcion, entrada.factorConsumoLkm,
                                               entrada.fechaInicio, sesion.documento)
    return responder(201, "Tipo de vehículo registrado correctamente", datos, funcionalidad="FUN-21")


@router.get(
    "/tipos-vehiculo",
    summary="HU-23 Consultar los tipos de vehículo con su factor de consumo vigente",
    description="Retorna los tipos de vehículo con el factor en L/km vigente en la fecha de consulta. Los tipos "
                "sin factor vigente se señalan con sinFactorVigente = true. El filtro por estado es opcional. "
                "Requiere el permiso FUN-23 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-23", ConsultarTiposVehiculo.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de tipos de vehículo exitosa", [
            {"idTipo": "TV-01", "nombre": "Camión sencillo", "estado": "activo", "factorVigenteLkm": 0.095},
            {"idTipo": "TV-04", "nombre": "Furgón eléctrico", "estado": "activo", "factorVigenteLkm": None,
             "sinFactorVigente": True}], None, "FUN-23"),
        **SIN_SESION,
        403: _sin_permiso("FUN-23", "No tiene permiso para consultar el catálogo"),
        404: ejemplo(404, "Sin resultados", None,
                     [{"campo": "estado", "detalle": "No hay tipos de vehículo inactivos"}], "FUN-23"),
        422: ejemplo(422, "Los criterios de consulta no son válidos", None,
                     [{"campo": "estado", "detalle": 'El estado debe ser "activo" o "inactivo"'}], "FUN-23"),
        503: {"description": ConsultarTiposVehiculo.MENSAJE_503},
    },
)
def consultar_tipos_vehiculo(
    estado: str | None = Query(None, description='"activo" o "inactivo"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-23", "No tiene permiso para consultar el catálogo")),
    db: Session = Depends(get_db),
):
    datos = ConsultarTiposVehiculo(db).ejecutar(estado)
    return responder(200, "Consulta de tipos de vehículo exitosa", datos, funcionalidad="FUN-23")


@router.post(
    "/tipos-vehiculo/{idTipo}/factores-consumo",
    summary="HU-22 Actualizar el factor de consumo de un tipo de vehículo desde una fecha",
    description="Cierra el factor vigente el día anterior a la nueva fecha y guarda el nuevo factor como vigente. "
                "Los recorridos ya calculados conservan el factor con que se calcularon. El tipo debe existir y "
                "estar activo. Requiere el permiso FUN-22 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-22", ActualizarFactorConsumo.MENSAJE_503),
    responses={
        201: ejemplo(201, "Factor de consumo actualizado correctamente", {
            "idTipo": "TV-03", "factorAnterior": {"valorLkm": 0.125, "vigenteHasta": "2026-12-31"},
            "factorNuevo": {"valorLkm": 0.118, "vigenteDesde": "2027-01-01"}}, None, "FUN-22"),
        **SIN_SESION,
        403: _sin_permiso("FUN-22", "No tiene permiso para actualizar el factor de consumo"),
        404: ejemplo(404, "Tipo de vehículo no encontrado", None,
                     [{"campo": "idTipo", "detalle": "No existe un tipo activo con el identificador TV-09"}],
                     "FUN-22"),
        422: ejemplo(422, "La fecha del nuevo factor no es válida", None, [
            {"campo": "fechaInicio", "detalle": "No puede ser anterior al inicio del factor vigente (2026-11-01)"}],
            "FUN-22"),
        503: {"description": ActualizarFactorConsumo.MENSAJE_503},
    },
)
def actualizar_factor_consumo(
    idTipo: str = Path(..., description="Identificador del tipo de vehículo, por ejemplo TV-03"),
    entrada: FactorConsumoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-22", "No tiene permiso para actualizar el factor de consumo")),
    db: Session = Depends(get_db),
):
    entrada = entrada or FactorConsumoEntrada()
    datos = ActualizarFactorConsumo(db).ejecutar(idTipo, entrada.factorConsumoLkm, entrada.fechaInicio,
                                                 sesion.documento)
    return responder(201, "Factor de consumo actualizado correctamente", datos, funcionalidad="FUN-22")


@router.get(
    "/tipos-vehiculo/{idTipo}/factores-consumo",
    summary="HU-24 Consultar el histórico de factores de consumo de un tipo de vehículo",
    description="Retorna todos los factores del tipo con sus fechas de inicio y fin y su responsable, del más "
                "reciente al más antiguo, señalando el vigente con vigente = true. Requiere el permiso FUN-24 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-24", ConsultarHistoricoConsumo.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta del histórico de factores exitosa", [
            {"valorLkm": 0.118, "vigenteDesde": "2027-01-01", "vigenteHasta": None, "responsable": "63456789",
             "vigente": True},
            {"valorLkm": 0.125, "vigenteDesde": "2026-11-01", "vigenteHasta": "2026-12-31", "responsable": "63456789",
             "vigente": False}], None, "FUN-24"),
        400: ejemplo(400, "El identificador del tipo de vehículo no es válido", None,
                     [{"campo": "idTipo", "detalle": "Debe tener el formato TV-XX"}], "FUN-24"),
        **SIN_SESION,
        403: _sin_permiso("FUN-24", "No tiene permiso para consultar el histórico"),
        404: ejemplo(404, "Tipo de vehículo no encontrado", None,
                     [{"campo": "idTipo", "detalle": "No existe un tipo con el identificador TV-09"}], "FUN-24"),
        503: {"description": ConsultarHistoricoConsumo.MENSAJE_503},
    },
)
def consultar_historico_consumo(
    idTipo: str = Path(..., description="Identificador del tipo de vehículo, por ejemplo TV-03"),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-24", "No tiene permiso para consultar el histórico")),
    db: Session = Depends(get_db),
):
    datos = ConsultarHistoricoConsumo(db).ejecutar(idTipo)
    return responder(200, "Consulta del histórico de factores exitosa", datos, funcionalidad="FUN-24")


@router.post(
    "/combustibles",
    summary="HU-26 Registrar un tipo de combustible con su factor de emisión y fuente oficial",
    description="Registra el combustible en estado «activo» y guarda su factor en kg CO₂/L como vigente desde la "
                "fecha indicada, junto con la fuente oficial. El valor que propone API-EXT-03 solo se guarda cuando "
                "el administrador lo confirma y lo envía; si API-EXT-03 no responde, el administrador puede digitar "
                "el factor manualmente. Requiere el permiso FUN-26 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-26", RegistrarCombustible.MENSAJE_503),
    responses={
        201: ejemplo(201, "Tipo de combustible registrado correctamente", {
            "idCombustible": "CB-01", "nombre": "Diésel", "estado": "activo", "factorEmisionKgCO2L": 2.6,
            "vigenteDesde": "2026-11-01", "fuente": FUENTE}, None, "FUN-26"),
        **SIN_SESION,
        403: _sin_permiso("FUN-26", "No tiene permiso para registrar combustibles"),
        409: ejemplo(409, "El combustible ya está registrado", None,
                     [{"campo": "nombre", "detalle": "Ya existe el combustible Diésel"}], "FUN-26"),
        422: ejemplo(422, "El factor de emisión no es válido", None,
                     [{"campo": "factorEmisionKgCO2L", "detalle": "Debe ser numérico y mayor que 0"}], "FUN-26"),
        503: {"description": RegistrarCombustible.MENSAJE_503},
    },
)
def registrar_combustible(
    entrada: CombustibleEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-26", "No tiene permiso para registrar combustibles")),
    db: Session = Depends(get_db),
):
    entrada = entrada or CombustibleEntrada()
    datos = RegistrarCombustible(db).ejecutar(entrada.nombre, entrada.descripcion, entrada.factorEmisionKgCO2L,
                                              entrada.fechaInicio, entrada.fuente, sesion.documento)
    return responder(201, "Tipo de combustible registrado correctamente", datos, funcionalidad="FUN-26")


@router.get(
    "/combustibles",
    summary="HU-28 Consultar los combustibles con su factor de emisión vigente",
    description="Retorna los combustibles con el factor en kg CO₂/L vigente en la fecha de consulta y su fuente. "
                "Los combustibles sin factor vigente se señalan con sinFactorVigente = true. El filtro por estado "
                "es opcional. Requiere el permiso FUN-28 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-28", ConsultarCombustibles.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta de combustibles exitosa", [
            {"idCombustible": "CB-01", "nombre": "Diésel", "estado": "activo", "factorVigenteKgCO2L": 2.6,
             "fuente": "Fuente oficial (valor ilustrativo)"},
            {"idCombustible": "CB-02", "nombre": "Gas natural vehicular", "estado": "activo", "factorVigenteKgCO2L": None,
             "fuente": None, "sinFactorVigente": True}], None, "FUN-28"),
        **SIN_SESION,
        403: _sin_permiso("FUN-28", "No tiene permiso para consultar el catálogo"),
        404: ejemplo(404, "Sin resultados", None,
                     [{"campo": "estado", "detalle": "No hay combustibles inactivos"}], "FUN-28"),
        422: ejemplo(422, "Los criterios de consulta no son válidos", None,
                     [{"campo": "estado", "detalle": 'El estado debe ser "activo" o "inactivo"'}], "FUN-28"),
        503: {"description": ConsultarCombustibles.MENSAJE_503},
    },
)
def consultar_combustibles(
    estado: str | None = Query(None, description='"activo" o "inactivo"'),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-28", "No tiene permiso para consultar el catálogo")),
    db: Session = Depends(get_db),
):
    datos = ConsultarCombustibles(db).ejecutar(estado)
    return responder(200, "Consulta de combustibles exitosa", datos, funcionalidad="FUN-28")


@router.post(
    "/combustibles/{idCombustible}/factores-emision",
    summary="HU-27 Actualizar el factor de emisión de un combustible desde una fecha",
    description="Cierra el factor vigente el día anterior a la nueva fecha y guarda el nuevo factor como vigente "
                "con su fuente. Los recorridos ya calculados conservan el factor con que se calcularon. El "
                "combustible debe existir y estar activo. Requiere el permiso FUN-27 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-27", ActualizarFactorEmision.MENSAJE_503),
    responses={
        201: ejemplo(201, "Factor de emisión actualizado correctamente", {
            "idCombustible": "CB-01", "factorAnterior": {"valorKgCO2L": 2.6, "vigenteHasta": "2026-12-31"},
            "factorNuevo": {"valorKgCO2L": 2.63, "vigenteDesde": "2027-01-01", "fuente": FUENTE}}, None, "FUN-27"),
        **SIN_SESION,
        403: _sin_permiso("FUN-27", "No tiene permiso para actualizar el factor de emisión"),
        404: ejemplo(404, "Combustible no encontrado", None,
                     [{"campo": "idCombustible", "detalle": "No existe un combustible activo con el identificador CB-09"}],
                     "FUN-27"),
        422: ejemplo(422, "La fecha del nuevo factor no es válida", None, [
            {"campo": "fechaInicio", "detalle": "No puede ser anterior al inicio del factor vigente (2026-11-01)"}],
            "FUN-27"),
        503: {"description": ActualizarFactorEmision.MENSAJE_503},
    },
)
def actualizar_factor_emision(
    idCombustible: str = Path(..., description="Identificador del combustible, por ejemplo CB-01"),
    entrada: FactorEmisionEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-27", "No tiene permiso para actualizar el factor de emisión")),
    db: Session = Depends(get_db),
):
    entrada = entrada or FactorEmisionEntrada()
    datos = ActualizarFactorEmision(db).ejecutar(idCombustible, entrada.factorEmisionKgCO2L, entrada.fechaInicio,
                                                 entrada.fuente, sesion.documento)
    return responder(201, "Factor de emisión actualizado correctamente", datos, funcionalidad="FUN-27")


@router.get(
    "/combustibles/{idCombustible}/factores-emision",
    summary="HU-29 Consultar el histórico de factores de emisión de un combustible",
    description="Retorna todos los factores del combustible con sus fechas, su fuente y su responsable, del más "
                "reciente al más antiguo, señalando el vigente con vigente = true. Requiere el permiso FUN-29 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-29", ConsultarHistoricoEmision.MENSAJE_503),
    responses={
        200: ejemplo(200, "Consulta del histórico de factores exitosa", [
            {"valorKgCO2L": 2.63, "vigenteDesde": "2027-01-01", "vigenteHasta": None,
             "fuente": "Fuente oficial (valor ilustrativo)", "responsable": "63456789", "vigente": True},
            {"valorKgCO2L": 2.6, "vigenteDesde": "2026-11-01", "vigenteHasta": "2026-12-31",
             "fuente": "Fuente oficial (valor ilustrativo)", "responsable": "63456789", "vigente": False}],
            None, "FUN-29"),
        400: ejemplo(400, "El identificador del combustible no es válido", None,
                     [{"campo": "idCombustible", "detalle": "Debe tener el formato CB-XX"}], "FUN-29"),
        **SIN_SESION,
        403: _sin_permiso("FUN-29", "No tiene permiso para consultar el histórico"),
        404: ejemplo(404, "Combustible no encontrado", None,
                     [{"campo": "idCombustible", "detalle": "No existe un combustible con el identificador CB-09"}], "FUN-29"),
        503: {"description": ConsultarHistoricoEmision.MENSAJE_503},
    },
)
def consultar_historico_emision(
    idCombustible: str = Path(..., description="Identificador del combustible, por ejemplo CB-01"),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-29", "No tiene permiso para consultar el histórico")),
    db: Session = Depends(get_db),
):
    datos = ConsultarHistoricoEmision(db).ejecutar(idCombustible)
    return responder(200, "Consulta del histórico de factores exitosa", datos, funcionalidad="FUN-29")
