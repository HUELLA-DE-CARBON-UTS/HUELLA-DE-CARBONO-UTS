from app.domain.exceptions.errores import DatosNoValidos

MENSAJE = "Los datos de la sede no son válidos"

CAMPOS_API = {"nombre": "name", "ciudad": "city", "direccion": "address", "responsable": "manager"}

CAMPOS = {
    "nombre": ("El nombre de la sede es obligatorio", 80),
    "ciudad": ("La ciudad es obligatoria", 60),
    "direccion": ("La dirección es obligatoria", 150),
    "responsable": ("El responsable es obligatorio", 100),
}


def limpiar(valor: str | None) -> str:
    return " ".join((valor or "").split())


def validar_obligatorios(datos: dict[str, str]) -> None:
    errores = []
    for campo, (mensaje_vacio, maximo) in CAMPOS.items():
        valor = datos.get(campo, "")
        if not valor:
            errores.append({"field": CAMPOS_API[campo], "detail": mensaje_vacio})
        elif len(valor) > maximo:
            errores.append({"field": CAMPOS_API[campo], "detail": f"El campo no puede superar {maximo} caracteres"})
    if errores:
        raise DatosNoValidos(MENSAJE, errores)
