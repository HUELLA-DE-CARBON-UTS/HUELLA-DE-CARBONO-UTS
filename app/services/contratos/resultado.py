from typing import Any

from app.domain.value_objects.fecha import ahora


def cuerpo_estandar(codigo: int, mensaje: str, datos: Any = None, errores: list[dict] | None = None,
                    funcionalidad: str | None = None) -> dict:
    return {
        "success": codigo < 400,
        "codigo": codigo,
        "message": mensaje,
        "data": datos,
        "errores": errores or [],
        "metadatos": {"funcionalidad": funcionalidad, "fecha": ahora().isoformat()},
    }
