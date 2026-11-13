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
