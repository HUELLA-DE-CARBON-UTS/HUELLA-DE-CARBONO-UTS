EVENTOS = ("ingreso", "intento_fallido", "operacion_rechazada", "salida")


def estado(valor: str | None) -> str | None:
    return valor


def evento(valor: str) -> str:
    return valor


def accion(valor: str) -> str:
    return valor


def estado_interno(valor: str, femenino: bool = False) -> str | None:
    if valor in ("activo", "activa"):
        return "activa" if femenino else "activo"
    if valor in ("inactivo", "inactiva"):
        return "inactiva" if femenino else "inactivo"
    return None


def evento_interno(valor: str) -> str | None:
    return valor if valor in EVENTOS else None
