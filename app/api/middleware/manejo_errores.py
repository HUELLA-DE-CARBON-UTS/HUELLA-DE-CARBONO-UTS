from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.schemas.respuesta import datos_de_ruta as _datos_de_ruta, responder
from app.domain.exceptions.errores import ErrorNegocio

TRADUCCIONES = {
    "missing": "El campo es obligatorio",
    "list_type": "Debe ser una lista",
    "string_type": "Debe ser un texto",
    "string_too_long": "El texto supera la longitud permitida",
    "json_invalid": "El cuerpo de la solicitud no es un JSON válido",
    "model_attributes_type": "El cuerpo de la solicitud debe ser un objeto JSON",
    "dict_type": "El cuerpo de la solicitud debe ser un objeto JSON",
}


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def error_negocio(request: Request, exc: ErrorNegocio):
        return responder(exc.codigo, exc.mensaje, None, exc.errores, _datos_de_ruta(request).get("x-funcionalidad"))

    @app.exception_handler(RequestValidationError)
    async def error_validacion(request: Request, exc: RequestValidationError):
        errores = [
            {"field": str(e["loc"][-1]), "detail": TRADUCCIONES.get(e["type"], e["msg"])}
            for e in exc.errors()
        ]
        return responder(422, "Los datos enviados no son válidos", None, errores,
                         _datos_de_ruta(request).get("x-funcionalidad"))

    @app.exception_handler(SQLAlchemyError)
    async def error_base_de_datos(request: Request, exc: SQLAlchemyError):
        datos = _datos_de_ruta(request)
        return responder(503, datos.get("x-mensaje-503", "El servicio no está disponible en este momento"), None,
                         [{"field": "database", "detail": "La base de datos no está disponible"}],
                         datos.get("x-funcionalidad"))
