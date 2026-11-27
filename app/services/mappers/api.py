ESTADOS = {"activo": "active", "activa": "active", "inactivo": "inactive", "inactiva": "inactive"}
EVENTOS = {"ingreso": "login", "intento_fallido": "failed_login", "operacion_rechazada": "rejected_operation",
           "salida": "logout"}
ACCIONES = {"creado": "created", "actualizado": "updated"}


def estado(valor: str | None) -> str | None:
    return ESTADOS.get(valor, valor)


def evento(valor: str) -> str:
    return EVENTOS.get(valor, valor)


def accion(valor: str) -> str:
    return ACCIONES.get(valor, valor)


def estado_interno(valor: str, femenino: bool = False) -> str | None:
    if valor == "active":
        return "activa" if femenino else "activo"
    if valor == "inactive":
        return "inactiva" if femenino else "inactivo"
    return None


def evento_interno(valor: str) -> str | None:
    return {v: k for k, v in EVENTOS.items()}.get(valor)
