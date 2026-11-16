from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.routing import Match

from app.services.contratos.resultado import cuerpo_estandar
"""Estructura estándar de las respuestas JSON (Tabla 22 del Parcial 1)."""

from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.value_objects.fecha import ahora


class ErrorCampo(BaseModel):
    campo: str
    detalle: str


class Metadatos(BaseModel):
    funcionalidad: str | None = None
    fecha: str


class RespuestaEstandar(BaseModel):
    estado: str
    codigo: int
    mensaje: str
    datos: Any = None
    errores: list[ErrorCampo] = []
    metadatos: Metadatos


def responder(codigo: int, mensaje: str, datos: Any = None, errores: list[dict] | None = None,
              funcionalidad: str | None = None, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=codigo, content=cuerpo_estandar(codigo, mensaje, datos, errores, funcionalidad),
                        headers=headers)


def ruta(funcionalidad: str, mensaje_503: str) -> dict:
    """Datos de la funcionalidad que se agregan a cada endpoint (openapi_extra).

    El manejador de errores los usa para llenar metadatos.funcionalidad y para
    responder con el mensaje de la historia cuando la base de datos no está disponible.
    """
    return {"x-funcionalidad": funcionalidad, "x-mensaje-503": mensaje_503}


def ejemplo(codigo: int, mensaje: str, datos: Any, errores: list[dict] | None, funcionalidad: str) -> dict:
    """Ejemplo de respuesta para la documentación de Swagger."""
    return {"content": {"application/json": {"example": {
        "estado": "exito" if codigo < 400 else "error", "codigo": codigo, "mensaje": mensaje,
        "datos": datos, "errores": errores or [],
        "metadatos": {"funcionalidad": funcionalidad, "fecha": "2026-11-03T09:15:00-05:00"},
    }}}}


def datos_de_ruta(request: Request) -> dict:
    """Funcionalidad y mensaje 503 del endpoint que atiende la solicitud."""
    for endpoint in request.app.routes:
        coincide, _ = endpoint.matches(request.scope)
        if coincide == Match.FULL:
            return getattr(endpoint, "openapi_extra", None) or {}
    return {}
              funcionalidad: str | None = None) -> JSONResponse:
    cuerpo = {
        "estado": "exito" if codigo < 400 else "error",
        "codigo": codigo,
        "mensaje": mensaje,
        "datos": datos,
        "errores": errores or [],
        "metadatos": {"funcionalidad": funcionalidad, "fecha": ahora().isoformat()},
    }
    return JSONResponse(status_code=codigo, content=cuerpo)
