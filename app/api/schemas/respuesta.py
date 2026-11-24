from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.routing import Match

from app.services.contratos.resultado import cuerpo_estandar


class ErrorItem(BaseModel):
    field: str
    detail: str


class Metadata(BaseModel):
    feature: str | None = None
    timestamp: str


class RespuestaEstandar(BaseModel):
    success: bool
    status: int
    message: str
    data: Any = None
    errors: list[ErrorItem] = []
    metadata: Metadata


def responder(codigo: int, mensaje: str, datos: Any = None, errores: list[dict] | None = None,
              funcionalidad: str | None = None, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=codigo, content=cuerpo_estandar(codigo, mensaje, datos, errores, funcionalidad),
                        headers=headers)


def ruta(funcionalidad: str, mensaje_503: str) -> dict:
    return {"x-funcionalidad": funcionalidad, "x-mensaje-503": mensaje_503}


def ejemplo(codigo: int, mensaje: str, datos: Any, errores: list[dict] | None, funcionalidad: str) -> dict:
    return {"content": {"application/json": {"example": {
        "success": codigo < 400, "status": codigo, "message": mensaje,
        "data": datos, "errors": errores or [],
        "metadata": {"feature": funcionalidad, "timestamp": "2026-11-03T09:15:00-05:00"},
    }}}}


def datos_de_ruta(request: Request) -> dict:
    for endpoint in request.app.routes:
        coincide, _ = endpoint.matches(request.scope)
        if coincide == Match.FULL:
            return getattr(endpoint, "openapi_extra", None) or {}
    return {}
