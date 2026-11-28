from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.distancias import get_servicio_distancias
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.recorrido import (
    CancelacionEntrada, CierreEntrada, CorreccionCierreEntrada, RecorridoEntrada, ReprogramacionEntrada)
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.gestion_recorridos import (
    CancelarRecorrido, CerrarRecorrido, CorregirCierre, ProgramarRecorrido, ReprogramarRecorrido)

router = APIRouter(prefix="/api/v1/recorridos", tags=["MOD-05 Gestión de Recorridos"])
SIN_SESION = {401: {"description": "No hay una sesión vigente"}}
CODIGO = Path(..., description="Código del recorrido, por ejemplo REC-0152")


def _sin_permiso(funcionalidad: str, mensaje: str) -> dict:
    return ejemplo(403, mensaje, None, [
        {"campo": "sesion", "detalle": f"El rol no tiene autorizada la operación {funcionalidad}"}], funcionalidad)


@router.post(
    "",
    summary="HU-36 Programar un recorrido asignándole un vehículo disponible",
    description="Crea el recorrido en estado «programado» con el tipo y el combustible del vehículo (IC-03) y deja el "
                "vehículo «asignado» (IC-04). El origen debe ser distinto del destino y la fecha no puede ser anterior "
                "a hoy (RN-05). La distancia estimada la entrega API-EXT-01; si no responde, el recorrido se programa "
                "sin distancia estimada. Requiere el permiso FUN-36 (IC-01).",
    response_model=RespuestaEstandar, status_code=201, openapi_extra=ruta("FUN-36", ProgramarRecorrido.MENSAJE_503),
    responses={
        201: ejemplo(201, "Recorrido programado correctamente", {
            "codigoRecorrido": "REC-0152", "placa": "TTK-482", "origen": "Bucaramanga", "destino": "Barranquilla",
            "fechaProgramada": "2026-11-18", "distanciaEstimadaKm": 392, "estado": "programado"}, None, "FUN-36"),
        **SIN_SESION,
        403: _sin_permiso("FUN-36", "No tiene permiso para programar recorridos"),
        404: ejemplo(404, "Vehículo no encontrado", None,
                     [{"campo": "placa", "detalle": "No existe un vehículo con la placa ABC-000"}], "FUN-36"),
        409: ejemplo(409, "El vehículo no está disponible", None,
                     [{"campo": "placa", "detalle": "El vehículo SXR-215 está asignado al recorrido REC-0160"}],
                     "FUN-36"),
        422: ejemplo(422, "Los datos del recorrido no son válidos", None,
                     [{"campo": "destino", "detalle": "El destino debe ser distinto del origen (RN-05)"}], "FUN-36"),
        503: {"description": ProgramarRecorrido.MENSAJE_503},
    },
)
def programar_recorrido(
    entrada: RecorridoEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-36", "No tiene permiso para programar recorridos")),
    db: Session = Depends(get_db),
    distancias=Depends(get_servicio_distancias),
):
    entrada = entrada or RecorridoEntrada()
    datos = ProgramarRecorrido(db, distancias).ejecutar(entrada.placa, entrada.origen, entrada.destino,
                                                        entrada.fechaProgramada, sesion.documento)
    return responder(201, "Recorrido programado correctamente", datos, funcionalidad="FUN-36")


@router.patch(
    "/{codigo}/programacion",
    summary="HU-37 Cambiar la fecha o el vehículo de un recorrido aún no cerrado",
    description="Solo se reprograman recorridos «programados». La nueva fecha no puede ser anterior a hoy. Si cambia el "
                "vehículo, el nuevo debe estar «disponible» (IC-03); el anterior queda «disponible» y el nuevo "
                "«asignado» (IC-04). El cambio queda en el historial con los valores anteriores, la fecha y el "
                "responsable. Requiere el permiso FUN-37 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-37", ReprogramarRecorrido.MENSAJE_503),
    responses={
        200: ejemplo(200, "Recorrido reprogramado correctamente", {
            "codigoRecorrido": "REC-0152", "placaAnterior": "TTK-482", "placaNueva": "WFN-731",
            "fechaProgramada": "2026-11-20"}, None, "FUN-37"),
        **SIN_SESION,
        403: _sin_permiso("FUN-37", "No tiene permiso para reprogramar recorridos"),
        404: ejemplo(404, "Recorrido no encontrado", None,
                     [{"campo": "codigoRecorrido", "detalle": "No existe el recorrido REC-9999"}], "FUN-37"),
        409: ejemplo(409, "El recorrido no se puede reprogramar", None,
                     [{"campo": "codigoRecorrido", "detalle": "El recorrido REC-0140 ya está cerrado"}], "FUN-37"),
        422: ejemplo(422, "Los datos de la reprogramación no son válidos", None,
                     [{"campo": "fechaProgramada", "detalle": "La fecha no puede ser anterior a hoy (RN-05)"}],
                     "FUN-37"),
        503: {"description": ReprogramarRecorrido.MENSAJE_503},
    },
)
def reprogramar_recorrido(
    codigo: str = CODIGO,
    entrada: ReprogramacionEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-37", "No tiene permiso para reprogramar recorridos")),
    db: Session = Depends(get_db),
):
    entrada = entrada or ReprogramacionEntrada()
    datos = ReprogramarRecorrido(db).ejecutar(codigo, entrada.fechaProgramada, entrada.placa, sesion.documento)
    return responder(200, "Recorrido reprogramado correctamente", datos, funcionalidad="FUN-37")


@router.patch(
    "/{codigo}/cancelacion",
    summary="HU-38 Cancelar un recorrido programado con su motivo",
    description="Solo se cancelan recorridos «programados». El recorrido queda «cancelado», no entra en ningún "
                "indicador, y el vehículo vuelve a «disponible» (IC-04). La cancelación queda con motivo, fecha y "
                "responsable. Requiere el permiso FUN-38 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-38", CancelarRecorrido.MENSAJE_503),
    responses={
        200: ejemplo(200, "Recorrido cancelado correctamente", {
            "codigoRecorrido": "REC-0149", "estado": "cancelado", "motivo": "El cliente aplazó el despacho",
            "placaLiberada": "SXR-215"}, None, "FUN-38"),
        **SIN_SESION,
        403: _sin_permiso("FUN-38", "No tiene permiso para cancelar recorridos"),
        404: ejemplo(404, "Recorrido no encontrado", None,
                     [{"campo": "codigoRecorrido", "detalle": "No existe el recorrido REC-9999"}], "FUN-38"),
        409: ejemplo(409, "El recorrido no se puede cancelar", None,
                     [{"campo": "codigoRecorrido", "detalle": "El recorrido REC-0140 ya está cerrado"}], "FUN-38"),
        422: ejemplo(422, "Los datos de la cancelación no son válidos", None,
                     [{"campo": "motivo", "detalle": "El motivo es obligatorio"}], "FUN-38"),
        503: {"description": CancelarRecorrido.MENSAJE_503},
    },
)
def cancelar_recorrido(
    codigo: str = CODIGO,
    entrada: CancelacionEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-38", "No tiene permiso para cancelar recorridos")),
    db: Session = Depends(get_db),
):
    entrada = entrada or CancelacionEntrada()
    datos = CancelarRecorrido(db).ejecutar(codigo, entrada.motivo, sesion.documento)
    return responder(200, "Recorrido cancelado correctamente", datos, funcionalidad="FUN-38")


@router.post(
    "/{codigo}/cierre",
    summary="HU-39 Cerrar un recorrido con su distancia y litros consumidos",
    description="Cierra un recorrido «programado» con la fecha, la distancia y los litros. La fecha de cierre no puede "
                "ser anterior a la programada. Ejecuta IC-05 (consumo estimado, eficiencia y emisiones con los "
                "factores vigentes en la fecha de cierre); si falta un factor, el recorrido queda cerrado y "
                "estadoCalculo = «pendiente». El vehículo vuelve a «disponible» (IC-04). Requiere el permiso FUN-39 "
                "(IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-39", CerrarRecorrido.MENSAJE_503),
    responses={
        200: ejemplo(200, "Recorrido cerrado correctamente", {
            "codigoRecorrido": "REC-0152", "placa": "TTK-482", "distanciaKm": 400, "consumoRegistradoL": 55.0,
            "consumoEstimadoL": 50.0, "rendimientoLkm": 0.1375, "desviacionPct": 10.0, "emisionesKgCO2": 143.0,
            "estadoCalculo": "completo"}, None, "FUN-39"),
        **SIN_SESION,
        403: _sin_permiso("FUN-39", "No tiene permiso para cerrar recorridos"),
        404: ejemplo(404, "Recorrido no encontrado", None,
                     [{"campo": "codigoRecorrido", "detalle": "No existe el recorrido REC-9999"}], "FUN-39"),
        409: ejemplo(409, "El recorrido no se puede cerrar en su estado actual", None,
                     [{"campo": "codigoRecorrido", "detalle": 'El recorrido REC-0149 está en estado "cancelado"'}],
                     "FUN-39"),
        422: ejemplo(422, "Los datos del cierre no son válidos", None,
                     [{"campo": "distanciaKm", "detalle": "Debe ser mayor que 0 (RN-05)"}], "FUN-39"),
        503: {"description": CerrarRecorrido.MENSAJE_503},
    },
)
def cerrar_recorrido(
    codigo: str = CODIGO,
    entrada: CierreEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso("FUN-39", "No tiene permiso para cerrar recorridos")),
    db: Session = Depends(get_db),
):
    entrada = entrada or CierreEntrada()
    datos = CerrarRecorrido(db).ejecutar(codigo, entrada.fechaCierre, entrada.distanciaKm,
                                         entrada.consumoRegistradoL, sesion.documento)
    return responder(200, "Recorrido cerrado correctamente", datos, funcionalidad="FUN-39")


@router.patch(
    "/{codigo}/cierre",
    summary="HU-40 Corregir la distancia o los litros de un recorrido ya cerrado",
    description="Solo se corrigen recorridos «cerrados». Los valores nuevos deben ser mayores que 0 y distintos de los "
                "actuales, y el motivo es obligatorio. Se guardan los valores anteriores, los nuevos, el motivo, la "
                "fecha y el responsable, y se recalcula con IC-18 usando los factores vigentes en la fecha del "
                "recorrido; el resultado anterior queda como versión histórica. Requiere el permiso FUN-40 (IC-01).",
    response_model=RespuestaEstandar, openapi_extra=ruta("FUN-40", CorregirCierre.MENSAJE_503),
    responses={
        200: ejemplo(200, "Cierre corregido y resultados recalculados", {
            "codigoRecorrido": "REC-0152", "valoresAnteriores": {"distanciaKm": 400, "consumoRegistradoL": 55.0},
            "valoresNuevos": {"distanciaKm": 400, "consumoRegistradoL": 52.0}, "consumoEstimadoL": 50.0,
            "desviacionPct": 4.0, "emisionesKgCO2": 135.2}, None, "FUN-40"),
        **SIN_SESION,
        403: _sin_permiso("FUN-40", "No tiene permiso para corregir el cierre de recorridos"),
        404: ejemplo(404, "Recorrido no encontrado", None,
                     [{"campo": "codigoRecorrido", "detalle": "No existe el recorrido REC-9999"}], "FUN-40"),
        409: ejemplo(409, "El recorrido no está cerrado", None,
                     [{"campo": "codigoRecorrido", "detalle": 'El recorrido REC-0160 está en estado "programado"'}],
                     "FUN-40"),
        422: ejemplo(422, "Los valores corregidos no son válidos", None, [
            {"campo": "consumoRegistradoL", "detalle": "Debe ser mayor que 0 y distinto del valor actual"}], "FUN-40"),
        503: {"description": CorregirCierre.MENSAJE_503},
    },
)
def corregir_cierre(
    codigo: str = CODIGO,
    entrada: CorreccionCierreEntrada | None = Body(None),
    sesion: SesionUsuario = Depends(requiere_permiso(
        "FUN-40", "No tiene permiso para corregir el cierre de recorridos")),
    db: Session = Depends(get_db),
):
    entrada = entrada or CorreccionCierreEntrada()
    datos = CorregirCierre(db).ejecutar(codigo, entrada.distanciaKm, entrada.consumoRegistradoL, entrada.motivo,
                                        sesion.documento)
    return responder(200, "Cierre corregido y resultados recalculados", datos, funcionalidad="FUN-40")
