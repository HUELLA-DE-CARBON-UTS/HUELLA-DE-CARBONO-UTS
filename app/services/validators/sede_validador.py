<<<<<<< HEAD
=======
"""Validaciones de PRO-16: campos obligatorios completos y dentro de su longitud."""

>>>>>>> feature/HU-01-registro-usuario
from app.domain.exceptions.errores import DatosNoValidos

MENSAJE = "Los datos de la sede no son válidos"

<<<<<<< HEAD
=======
# campo: (mensaje si está vacío, longitud máxima)
>>>>>>> feature/HU-01-registro-usuario
CAMPOS = {
    "nombre": ("El nombre de la sede es obligatorio", 80),
    "ciudad": ("La ciudad es obligatoria", 60),
    "direccion": ("La dirección es obligatoria", 150),
    "responsable": ("El responsable es obligatorio", 100),
}


def limpiar(valor: str | None) -> str:
<<<<<<< HEAD
=======
    """Quita espacios sobrantes al inicio, al final y entre palabras."""
>>>>>>> feature/HU-01-registro-usuario
    return " ".join((valor or "").split())


def validar_obligatorios(datos: dict[str, str]) -> None:
    errores = []
    for campo, (mensaje_vacio, maximo) in CAMPOS.items():
        valor = datos.get(campo, "")
        if not valor:
            errores.append({"campo": campo, "detalle": mensaje_vacio})
        elif len(valor) > maximo:
            errores.append({"campo": campo, "detalle": f"El campo no puede superar {maximo} caracteres"})
    if errores:
        raise DatosNoValidos(MENSAJE, errores)
