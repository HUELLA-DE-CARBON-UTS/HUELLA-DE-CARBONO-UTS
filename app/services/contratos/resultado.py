"""Estructura estándar de respuesta (Tabla 22 del Parcial 1), usada por la API
y por los contratos internos como IC-01."""

from typing import Any

from app.domain.value_objects.fecha import ahora


def cuerpo_estandar(codigo: int, mensaje: str, datos: Any = None, errores: list[dict] | None = None,
                    funcionalidad: str | None = None) -> dict:
    return {
        "estado": "exito" if codigo < 400 else "error",
        "codigo": codigo,
        "mensaje": mensaje,
        "datos": datos,
        "errores": errores or [],
        "metadatos": {"funcionalidad": funcionalidad, "fecha": ahora().isoformat()},
    }
