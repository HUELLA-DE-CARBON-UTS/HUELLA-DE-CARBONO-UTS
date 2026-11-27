import re

from app.services.validators.catalogo_validador import limpiar, numero

FORMATO_PLACA = re.compile(r"^[A-Z]{3}-\d{3}$")
ESTADOS = {"disponible": "disponible", "asignado": "asignado", "fuera_de_servicio": "fuera de servicio"}


def normalizar_placa(valor) -> str:
    return limpiar(valor).upper()


def error_placa(placa: str) -> dict | None:
    if not placa:
        return {"campo": "placa", "detalle": "La placa es obligatoria"}
    if not FORMATO_PLACA.match(placa):
        return {"campo": "placa", "detalle": "La placa debe tener el formato AAA-000"}
    return None


def capacidad(valor) -> float | None:
    cantidad = numero(valor)
    return cantidad if cantidad is not None and cantidad > 0 else None


def error_capacidad(valor) -> dict | None:
    if capacidad(valor) is None:
        return {"campo": "capacidadT", "detalle": "La capacidad debe ser mayor que 0"}
    return None


def error_obligatorio(campo: str, valor: str, mensaje: str) -> dict | None:
    return None if valor else {"campo": campo, "detalle": mensaje}


def estado_api(valor: str) -> str:
    return ESTADOS.get(valor, valor)
