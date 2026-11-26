import re
from datetime import date

from app.domain.exceptions.errores import DatosNoValidos

ESTADOS = ("active", "inactive")
FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def limpiar(valor) -> str:
    return " ".join(valor.split()) if isinstance(valor, str) else ""


def numero(valor) -> float | None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return float(valor)


def fecha(valor) -> date | None:
    if not isinstance(valor, str) or not FORMATO_FECHA.match(valor.strip()):
        return None
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        return None


def error_texto(campo: str, valor: str, mensaje_vacio: str, maximo: int) -> dict | None:
    if not valor:
        return {"field": campo, "detail": mensaje_vacio}
    if len(valor) > maximo:
        return {"field": campo, "detail": f"El campo no puede superar {maximo} caracteres"}
    return None


def error_fecha(campo: str, valor: date | None) -> dict | None:
    if valor is None:
        return {"field": campo, "detail": "La fecha de inicio es obligatoria y debe tener el formato AAAA-MM-DD"}
    return None


def error_estado(estado: str) -> dict | None:
    if estado not in ESTADOS:
        return {"field": "status", "detail": 'El estado debe ser "active" o "inactive"'}
    return None


def lanzar(errores: list[dict | None], mensaje_general: str, campo_factor: str, mensaje_factor: str) -> None:
    errores = [e for e in errores if e]
    if not errores:
        return
    if all(e["field"] == campo_factor for e in errores):
        raise DatosNoValidos(mensaje_factor, errores)
    raise DatosNoValidos(mensaje_general, errores)
