import re
from datetime import date

from app.domain.exceptions.errores import DatosNoValidos, SolicitudIncorrecta

ESTADOS = ("activo", "inactivo")
FORMATO_ID = {"TV": re.compile(r"^TV-\d{2,}$"), "CB": re.compile(r"^CB-\d{2,}$")}
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
        return {"campo": campo, "detalle": mensaje_vacio}
    if len(valor) > maximo:
        return {"campo": campo, "detalle": f"El campo no puede superar {maximo} caracteres"}
    return None


def error_fecha(campo: str, valor: date | None) -> dict | None:
    if valor is None:
        return {"campo": campo, "detalle": "La fecha de inicio es obligatoria y debe tener el formato AAAA-MM-DD"}
    return None


def error_estado(estado: str) -> dict | None:
    if estado not in ESTADOS:
        return {"campo": "estado", "detalle": 'El estado debe ser "activo" o "inactivo"'}
    return None


def lanzar(errores: list[dict | None], mensaje_general: str, campo_factor: str, mensaje_factor: str) -> None:
    errores = [e for e in errores if e]
    if not errores:
        return
    if all(e["campo"] == campo_factor for e in errores):
        raise DatosNoValidos(mensaje_factor, errores)
    raise DatosNoValidos(mensaje_general, errores)


def validar_identificador(valor: str, prefijo: str, campo: str, mensaje: str) -> str:
    identificador = (valor or "").strip().upper()
    if not FORMATO_ID[prefijo].match(identificador):
        raise SolicitudIncorrecta(mensaje, [{"campo": campo, "detalle": f"Debe tener el formato {prefijo}-XX"}])
    return identificador
