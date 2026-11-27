from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.distancias import get_servicio_distancias
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.recorrido import CancelacionEntrada, RecorridoEntrada, ReprogramacionEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.gestion_recorridos import CancelarRecorrido, ProgramarRecorrido, ReprogramarRecorrido

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
