"""Validaciones de PRO-11: nombre diligenciado, al menos un permiso y
permisos que correspondan a operaciones existentes del sistema."""

from app.domain.exceptions.errores import DatosNoValidos

MENSAJE = "La configuración del rol no es válida"


def normalizar_permisos(permisos: list[str]) -> list[str]:
    """Quita espacios y duplicados conservando el orden recibido."""
    vistos: list[str] = []
    for p in permisos:
        codigo = p.strip().upper()
        if codigo and codigo not in vistos:
            vistos.append(codigo)
    return vistos


def validar_datos_basicos(nombre: str, permisos: list[str]) -> None:
    errores = []
    if not nombre.strip():
        errores.append({"campo": "nombre", "detalle": "El nombre del rol es obligatorio"})
    elif len(nombre.strip()) > 60:
        errores.append({"campo": "nombre", "detalle": "El nombre del rol no puede superar 60 caracteres"})
    if not permisos:
        errores.append({"campo": "permisos", "detalle": "El rol debe tener al menos un permiso"})
    if errores:
        raise DatosNoValidos(MENSAJE, errores)


def validar_operaciones(permisos: list[str], existentes: set[str]) -> None:
    errores = [
        {"campo": "permisos", "detalle": f"La operación {p} no existe en el sistema"}
        for p in permisos if p not in existentes
    ]
    if errores:
        raise DatosNoValidos(MENSAJE, errores)
