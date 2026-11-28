import re
from datetime import date

from app.domain.exceptions.errores import DatosNoValidos, SolicitudIncorrecta
from app.services.validators.catalogo_validador import fecha, limpiar, numero
from app.services.validators.vehiculo_validador import FORMATO_PLACA

FORMATO_CODIGO = re.compile(r"^REC-\d{4,}$")
FORMATO_FECHA_NO_VALIDO = "Formato de fecha no válido. Debe ser YYYY-MM-DD"
ESTADOS = ("programado", "cerrado", "cancelado")


def normalizar_codigo(valor) -> str:
    return limpiar(valor).upper()


def validar_codigo(valor) -> str:
    codigo = normalizar_codigo(valor)
    if not FORMATO_CODIGO.match(codigo):
        raise SolicitudIncorrecta("El código del recorrido no es válido", [
            {"campo": "codigoRecorrido", "detalle": "Debe tener el formato REC-0000"}])
    return codigo


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


def rango_opcional(fecha_inicial, fecha_final) -> tuple[date | None, date | None]:
    errores = []
    if limpiar(fecha_inicial) and fecha(fecha_inicial) is None:
        errores.append({"campo": "fechaInicial", "detalle": FORMATO_FECHA_NO_VALIDO})
    if limpiar(fecha_final) and fecha(fecha_final) is None:
        errores.append({"campo": "fechaFinal", "detalle": FORMATO_FECHA_NO_VALIDO})
    if errores:
        raise DatosNoValidos("Los parámetros de consulta no son válidos", errores)
    inicio, fin = fecha(fecha_inicial), fecha(fecha_final)
    if inicio and fin and inicio > fin:
        raise DatosNoValidos("El rango de fechas no es válido", [
            {"campo": "fechaInicial", "detalle": "La fecha inicial no puede ser posterior a la fecha final"}])
    return inicio, fin


def rango_obligatorio(fecha_inicial, fecha_final) -> tuple[date, date]:
    errores = [e for e in [error_fecha("fechaInicial", fecha_inicial), error_fecha("fechaFinal", fecha_final)] if e]
    if errores:
        raise DatosNoValidos("Los parámetros de consulta no son válidos", errores)
    return rango_opcional(fecha_inicial, fecha_final)


def en_rango(dia: date | None, inicio: date | None, fin: date | None) -> bool:
    if dia is None:
        return False
    return (inicio is None or dia >= inicio) and (fin is None or dia <= fin)
