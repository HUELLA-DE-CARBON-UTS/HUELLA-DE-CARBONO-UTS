"""Convierte los errores en la respuesta JSON estándar."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.schemas.respuesta import responder
from app.domain.exceptions.errores import ErrorNegocio

TRADUCCIONES = {
    "missing": "El campo es obligatorio",
    "list_type": "Debe ser una lista",
    "string_type": "Debe ser un texto",
    "string_too_long": "El texto supera la longitud permitida",
    "json_invalid": "El cuerpo de la solicitud no es un JSON válido",
}

# Funcionalidad asociada a cada ruta, para el campo metadatos.funcionalidad.
FUNCIONALIDAD_POR_RUTA = {"/api/v1/roles/": "FUN-11"}


def _funcionalidad(request: Request) -> str | None:
    for prefijo, fun in FUNCIONALIDAD_POR_RUTA.items():
        if request.url.path.startswith(prefijo):
            return fun
    return None


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def error_negocio(request: Request, exc: ErrorNegocio):
        return responder(exc.codigo, exc.mensaje, None, exc.errores, _funcionalidad(request))

    @app.exception_handler(RequestValidationError)
    async def error_validacion(request: Request, exc: RequestValidationError):
        errores = [
            {"campo": str(e["loc"][-1]), "detalle": TRADUCCIONES.get(e["type"], e["msg"])}
            for e in exc.errors()
        ]
        return responder(422, "Los datos enviados no son válidos", None, errores, _funcionalidad(request))

    @app.exception_handler(SQLAlchemyError)
    async def error_base_de_datos(request: Request, exc: SQLAlchemyError):
        return responder(503, "El servicio no está disponible en este momento", None,
                         [{"campo": "baseDeDatos", "detalle": "La base de datos no está disponible"}],
                         _funcionalidad(request))
