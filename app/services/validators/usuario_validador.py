import re

from app.domain.exceptions.errores import DatosNoValidos

FORMATO_DOCUMENTO = re.compile(r"^\d{6,12}$")
FORMATO_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
FORMATO_TELEFONO = re.compile(r"^\d{7,15}$")
ESTADOS = ("activo", "inactivo")


def limpiar(valor: str | None) -> str:
    return " ".join((valor or "").split())


def error_documento(documento: str) -> dict | None:
    if not documento:
        return {"campo": "documento", "detalle": "El documento es obligatorio"}
    if not FORMATO_DOCUMENTO.match(documento):
        return {"campo": "documento", "detalle": "El documento debe tener entre 6 y 12 dígitos, sin puntos ni letras"}
    return None


def error_correo(correo: str) -> dict | None:
    if not correo:
        return {"campo": "correo", "detalle": "El correo es obligatorio"}
    if len(correo) > 120 or not FORMATO_CORREO.match(correo):
        return {"campo": "correo", "detalle": "El correo no tiene un formato válido"}
    return None


def error_telefono(telefono: str) -> dict | None:
    if not telefono:
        return {"campo": "telefono", "detalle": "El teléfono es obligatorio"}
    if not telefono.isdigit():
        return {"campo": "telefono", "detalle": "El teléfono debe contener solo dígitos"}
    if not FORMATO_TELEFONO.match(telefono):
        return {"campo": "telefono", "detalle": "El teléfono debe tener entre 7 y 15 dígitos"}
    return None


def error_estado(estado: str) -> dict | None:
    if estado not in ESTADOS:
        return {"campo": "estado", "detalle": 'El estado debe ser "activo" o "inactivo"'}
    return None


def validar_registro(datos: dict[str, str]) -> None:
    errores = [
        error_documento(datos["documento"]),
        None if datos["nombres"] else {"campo": "nombres", "detalle": "Los nombres son obligatorios"},
        {"campo": "nombres", "detalle": "Los nombres no pueden superar 120 caracteres"} if len(datos["nombres"]) > 120 else None,
        error_correo(datos["correo"]),
        error_telefono(datos["telefono"]),
        None if datos["rol"] else {"campo": "rol", "detalle": "El rol inicial es obligatorio"},
        None if datos["sede"] else {"campo": "sede", "detalle": "La sede inicial es obligatoria"},
    ]
    errores = [e for e in errores if e]
    if errores:
        raise DatosNoValidos("Los datos del usuario no son válidos", errores)
