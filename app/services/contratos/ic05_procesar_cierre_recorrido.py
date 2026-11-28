from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.entities.recorrido import ResultadoRecorrido
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic02_consultar_catalogo_vigente import nombre_en_catalogo
from app.services.contratos.ic06_obtener_factor_consumo_vigente import obtener_factor_consumo_vigente
from app.services.contratos.ic07_obtener_factor_emision_vigente import obtener_factor_emision_vigente
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


def emisiones(db: Session, codigo: str, consumo_registrado, id_combustible: str, fecha_cierre) -> tuple:
    dia, error = _fecha_cierre(fecha_cierre)
    if error:
        return 422, "Los datos del recorrido no son válidos", None, [error]
    if v.error_positivo("consumoRegistradoL", consumo_registrado):
        return 422, "El consumo registrado no es válido", None, [
            v.error_positivo("consumoRegistradoL", consumo_registrado)]
    factor = obtener_factor_emision_vigente(db, id_combustible, dia)
    if factor is None:
        nombre = nombre_en_catalogo(db, "combustible", id_combustible)
        return 422, "Cálculo pendiente: no existe factor de emisión vigente", None, [
            {"campo": "combustible", "detalle": f"El combustible {nombre} no tiene factor vigente al {dia.isoformat()}"}]
    registrado = v.positivo(consumo_registrado)
    return 200, "Emisiones calculadas", {
        "codigoRecorrido": codigo, "consumoRegistradoL": registrado,
        "factorEmisionKgCO2L": factor["factorEmisionKgCO2L"], "fuente": factor["fuente"],
        "emisionesKgCO2": round(registrado * factor["factorEmisionKgCO2L"], 2), "idFactor": factor["idFactor"]}, []


def calcular_resultado(db: Session, codigo: str, distancia: float, consumo: float, id_tipo: str,
                       id_combustible: str, fecha_cierre: date, version: int = 1) -> ResultadoRecorrido:
    resultado = ResultadoRecorrido(codigo=codigo, distancia_km=distancia, consumo_registrado_l=consumo,
                                   version=version)
    codigo_http, _, datos, errores = consumo_estimado(db, codigo, distancia, id_tipo, fecha_cierre)
    if codigo_http == 200:
        resultado.estado_consumo = "completo"
        resultado.id_factor_consumo = datos["idFactor"]
        resultado.factor_consumo_lkm = datos["factorConsumoLkm"]
        resultado.consumo_estimado_l = datos["consumoEstimadoL"]
        _, _, datos_eficiencia, _ = eficiencia(codigo, consumo, distancia, resultado.consumo_estimado_l)
        resultado.rendimiento_lkm = datos_eficiencia["rendimientoLkm"]
        resultado.desviacion_pct = datos_eficiencia["desviacionPct"]
    else:
        nombre = nombre_en_catalogo(db, "tipo", id_tipo)
        resultado.causa_consumo = f"El tipo {nombre} no tiene factor de consumo vigente"

    codigo_http, _, datos, _ = emisiones(db, codigo, consumo, id_combustible, fecha_cierre)
    if codigo_http == 200:
        resultado.estado_emisiones = "completo"
        resultado.id_factor_emision = datos["idFactor"]
        resultado.factor_emision_kgco2l = datos["factorEmisionKgCO2L"]
        resultado.fuente_emision = datos["fuente"]
        resultado.emisiones_kgco2 = datos["emisionesKgCO2"]
    else:
        nombre = nombre_en_catalogo(db, "combustible", id_combustible)
        resultado.causa_emisiones = f"El combustible {nombre} no tiene factor de emisión vigente"
    return resultado


def resumen(resultado: ResultadoRecorrido) -> dict:
    return {"consumoEstimadoL": resultado.consumo_estimado_l, "rendimientoLkm": resultado.rendimiento_lkm,
            "desviacionPct": resultado.desviacion_pct, "emisionesKgCO2": resultado.emisiones_kgco2,
            "estadoCalculo": "completo" if resultado.completo() else "pendiente"}


def procesar_cierre_recorrido(db: Session, codigo: str, distancia: float, consumo: float, id_tipo: str,
                              id_combustible: str, fecha_cierre: date) -> ResultadoRecorrido:
    resultado = calcular_resultado(db, codigo, distancia, consumo, id_tipo, id_combustible, fecha_cierre)
    RecorridoRepositorioSQLAlchemy(db).guardar_resultado(resultado)
    return resultado


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


def calcular_emisiones(db: Session, codigo: str, consumo_registrado, id_combustible: str, fecha_cierre) -> dict:
    return _contrato("FUN-51", "No fue posible calcular las emisiones del recorrido", emisiones,
                     db, codigo, consumo_registrado, id_combustible, fecha_cierre)
