from fastapi import FastAPI
from fastapi.routing import APIRoute


def conservar_nulos_en_ejemplos(app: FastAPI) -> None:
    generar = app.openapi

    def openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        esquema = generar()
        for ruta in app.routes:
            if not isinstance(ruta, APIRoute):
                continue
            operaciones = esquema["paths"].get(ruta.path_format, {})
            for codigo, respuesta in (ruta.responses or {}).items():
                ejemplo = respuesta.get("content", {}).get("application/json", {}).get("example")
                if ejemplo is None:
                    continue
                for metodo in ruta.methods:
                    destino = operaciones.get(metodo.lower(), {}).get("responses", {}).get(str(codigo))
                    if destino and "content" in destino:
                        destino["content"]["application/json"]["example"] = ejemplo
        return esquema

    app.openapi = openapi
