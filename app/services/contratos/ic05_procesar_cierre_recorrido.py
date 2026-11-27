from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.contratos.ic02_consultar_catalogo_vigente import nombre_en_catalogo
from app.services.contratos.ic06_obtener_factor_consumo_vigente import obtener_factor_consumo_vigente
from app.services.contratos.resultado import cuerpo_estandar
from app.services.validators import recorrido_validador as v
from app.services.validators.catalogo_validador import fecha

ERROR_BD = [{"campo": "baseDeDatos", "detalle": "La base de datos no está disponible"}]


def _fecha_cierre(valor) -> tuple[date | None, dict | None]:
    if isinstance(valor, date):
        return valor, None
    dia = fecha(valor)
    if dia is None:
        return None, {"campo": "fechaCierre", "detalle": v.FORMATO_FECHA_NO_VALIDO}
    return dia, None


def consumo_estimado(db: Session, codigo: str, distancia, id_tipo: str, fecha_cierre) -> tuple:
    dia, error = _fecha_cierre(fecha_cierre)
    if error:
        return 422, "Los datos del recorrido no son válidos", None, [error]
    if v.error_positivo("distanciaKm", distancia):
        return 422, "La distancia del recorrido no es válida", None, [v.error_positivo("distanciaKm", distancia)]
    factor = obtener_factor_consumo_vigente(db, id_tipo, dia)
    if factor is None:
        nombre = nombre_en_catalogo(db, "tipo", id_tipo)
        return 422, "Cálculo pendiente: no existe factor de consumo vigente", None, [
            {"campo": "tipoVehiculo", "detalle": f"El tipo {nombre} no tiene factor vigente al {dia.isoformat()}"}]
    distancia = v.positivo(distancia)
    return 200, "Consumo estimado calculado", {
        "codigoRecorrido": codigo, "distanciaKm": distancia, "factorConsumoLkm": factor["factorConsumoLkm"],
        "idFactor": factor["idFactor"], "consumoEstimadoL": round(distancia * factor["factorConsumoLkm"], 2)}, []


def _contrato(funcionalidad: str, mensaje_503: str, calculo, *argumentos) -> dict:
    try:
        codigo_http, mensaje, datos, errores = calculo(*argumentos)
    except SQLAlchemyError:
        return cuerpo_estandar(503, mensaje_503, None, ERROR_BD, funcionalidad)
    if datos is not None and funcionalidad == "FUN-51":
        datos = {clave: valor for clave, valor in datos.items() if clave != "idFactor"}
    return cuerpo_estandar(codigo_http, mensaje, datos, errores, funcionalidad)


def calcular_consumo_estimado(db: Session, codigo: str, distancia, id_tipo: str, fecha_cierre) -> dict:
    return _contrato("FUN-46", "No fue posible calcular el consumo estimado", consumo_estimado,
                     db, codigo, distancia, id_tipo, fecha_cierre)
