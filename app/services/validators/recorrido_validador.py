from app.services.validators.catalogo_validador import fecha, limpiar
from app.services.validators.vehiculo_validador import FORMATO_PLACA
FORMATO_FECHA_NO_VALIDO = "Formato de fecha no válido. Debe ser YYYY-MM-DD"


def normalizar_codigo(valor) -> str:
    return limpiar(valor).upper()


def error_fecha(campo: str, valor) -> dict | None:
    if not limpiar(valor):
        return {"campo": campo, "detalle": "La fecha es obligatoria"}
    if fecha(valor) is None:
        return {"campo": campo, "detalle": FORMATO_FECHA_NO_VALIDO}
    return None


def error_placa(placa: str) -> dict | None:
    if placa and not FORMATO_PLACA.match(placa):
        return {"campo": "placa", "detalle": "La placa debe tener el formato AAA-000"}
    return None
