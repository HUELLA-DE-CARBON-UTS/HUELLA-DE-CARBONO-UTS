from app.services.validators.catalogo_validador import fecha, limpiar, numero
from app.services.validators.vehiculo_validador import FORMATO_PLACA
FORMATO_FECHA_NO_VALIDO = "Formato de fecha no válido. Debe ser YYYY-MM-DD"


def normalizar_codigo(valor) -> str:
    return limpiar(valor).upper()


def positivo(valor) -> float | None:
    cantidad = numero(valor)
    return cantidad if cantidad is not None and cantidad > 0 else None


def error_positivo(campo: str, valor, detalle: str = "Debe ser mayor que 0 (RN-05)") -> dict | None:
    if numero(valor) is None:
        return {"campo": campo, "detalle": "Debe ser un número mayor que 0"}
    if positivo(valor) is None:
        return {"campo": campo, "detalle": detalle}
    return None


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
