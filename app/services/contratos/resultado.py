from typing import Any

from app.domain.value_objects.fecha import ahora


def cuerpo_estandar(codigo: int, mensaje: str, datos: Any = None, errores: list[dict] | None = None,
                    funcionalidad: str | None = None) -> dict:
    return {
        "success": codigo < 400,
        "status": codigo,
        "message": mensaje,
        "data": datos,
        "errors": errores or [],
        "metadata": {"feature": funcionalidad, "timestamp": ahora().isoformat()},
    }
