import re
from datetime import date, datetime, timedelta

from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado
from app.domain.value_objects.fecha import ZONA_COLOMBIA, texto
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import BitacoraRepositorioSQLAlchemy
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion

MENSAJE_503 = "No fue posible consultar la bitácora de accesos"
TIPOS_EVENTO = ("ingreso", "intento_fallido", "operacion_rechazada", "salida")
FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def leer_fecha(valor: str | None, campo: str, nombre: str) -> tuple[date | None, dict | None]:
    valor = (valor or "").strip()
    if not valor:
        return None, {"campo": campo, "detalle": f"La {nombre} es obligatoria"}
    try:
        if not FORMATO_FECHA.match(valor):
            raise ValueError
        return date.fromisoformat(valor), None
    except ValueError:
        return None, {"campo": campo, "detalle": "Formato de fecha no válido. Debe ser YYYY-MM-DD"}


def validar_consulta(fecha_inicial, fecha_final, tipo_evento) -> tuple[date, date]:
    inicial, error_inicial = leer_fecha(fecha_inicial, "fechaInicial", "fecha inicial")
    final, error_final = leer_fecha(fecha_final, "fechaFinal", "fecha final")
    errores = [e for e in (error_inicial, error_final) if e]
    if tipo_evento and tipo_evento not in TIPOS_EVENTO:
        errores.append({"campo": "tipoEvento",
                        "detalle": "El tipo de evento debe ser ingreso, intento_fallido, operacion_rechazada o salida"})
    if errores:
        raise DatosNoValidos("Los datos de la consulta no son válidos", errores)
    if inicial > final:
        raise DatosNoValidos("El rango de fechas no es válido", [
            {"campo": "fechaInicial", "detalle": "La fecha inicial no puede ser posterior a la fecha final"}])
    return inicial, final


class ConsultarBitacora:
    def __init__(self, db):
        self.db = db
        self.bitacora = BitacoraRepositorioSQLAlchemy(db)

    def ejecutar(self, fecha_inicial, fecha_final, usuario=None, tipo_evento=None) -> list[dict]:
        usuario = (usuario or "").strip() or None
        tipo_evento = (tipo_evento or "").strip().lower() or None
        inicial, final = validar_consulta(fecha_inicial, fecha_final, tipo_evento)
        desde = datetime.combine(inicial, datetime.min.time(), ZONA_COLOMBIA)
        hasta = datetime.combine(final + timedelta(days=1), datetime.min.time(), ZONA_COLOMBIA)

        with transaccion(self.db, MENSAJE_503):
            eventos = self.bitacora.consultar(desde, hasta, usuario,
                                              api.evento_interno(tipo_evento) if tipo_evento else None)
        if not eventos:
            raise NoEncontrado("Sin registros en el periodo", [
                {"campo": "fechaInicial", "detalle": f"No hay eventos entre {inicial} y {final}"}])
        return [{"usuario": e.usuario, "tipoEvento": api.evento(e.tipo_evento), "operacion": e.operacion,
                 "fecha": texto(e.fecha)} for e in eventos]
