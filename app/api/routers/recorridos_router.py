from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.distancias import get_servicio_distancias
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.recorrido import RecorridoEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.services.use_cases.gestion_recorridos import ProgramarRecorrido

router = APIRouter(prefix="/api/v1/recorridos", tags=["MOD-05 Gestión de Recorridos"])
SIN_SESION = {401: {"description": "No hay una sesión vigente"}}


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
