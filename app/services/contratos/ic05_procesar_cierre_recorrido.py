from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.contratos.ic02_consultar_catalogo_vigente import nombre_en_catalogo
from app.services.contratos.ic06_obtener_factor_consumo_vigente import obtener_factor_consumo_vigente
from app.services.contratos.resultado import cuerpo_estandar
from app.services.validators import recorrido_validador as v
from app.services.validators.catalogo_validador import fecha

ERROR_BD = [{"campo": "baseDeDatos", "detalle": "La base de datos no está disponible"}]


def interpretar(desviacion: float) -> str:
    if desviacion > 0:
        return "consumo superior al esperado"
    if desviacion < 0:
        return "consumo inferior al esperado"
    return "consumo igual al esperado"


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


def eficiencia(codigo: str, consumo_registrado, distancia, consumo_estimado_l) -> tuple:
    errores = [e for e in [v.error_positivo("consumoRegistradoL", consumo_registrado),
                           v.error_positivo("distanciaKm", distancia, "Debe ser un número mayor que 0")] if e]
    if errores:
        return 422, "Los datos del recorrido no son válidos", None, errores
    if v.positivo(consumo_estimado_l) is None:
        return 422, "No es posible evaluar la eficiencia", None, [
            {"campo": "consumoEstimadoL", "detalle": "El consumo estimado está pendiente por falta de factor vigente"}]
    registrado, distancia = v.positivo(consumo_registrado), v.positivo(distancia)
    consumo_estimado_l = v.positivo(consumo_estimado_l)
    desviacion = round((registrado - consumo_estimado_l) / consumo_estimado_l * 100, 2)
    return 200, "Eficiencia evaluada", {
        "codigoRecorrido": codigo, "consumoRegistradoL": registrado, "consumoEstimadoL": consumo_estimado_l,
        "rendimientoLkm": round(registrado / distancia, 4), "desviacionPct": desviacion,
        "interpretacion": interpretar(desviacion)}, []


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


def evaluar_eficiencia(codigo: str, consumo_registrado, distancia, consumo_estimado_l) -> dict:
    return _contrato("FUN-47", "No fue posible evaluar la eficiencia del recorrido", eficiencia,
                     codigo, consumo_registrado, distancia, consumo_estimado_l)
