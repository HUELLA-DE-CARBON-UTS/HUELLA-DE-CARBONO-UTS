from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.entities.recorrido import ResultadoRecorrido
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic05_procesar_cierre_recorrido import ERROR_BD, calcular_resultado
from app.services.contratos.resultado import cuerpo_estandar
from app.services.validators import recorrido_validador as v


def _sin_resultado_previo(codigo: str, recorrido, anterior) -> tuple | None:
    if recorrido is None or recorrido.estado != "cerrado":
        return 409, "El recorrido no tiene un resultado previo", None, [
            {"campo": "codigoRecorrido", "detalle": f"El recorrido {codigo} no está cerrado"}]
    if anterior is None:
        return 409, "El recorrido no tiene un resultado previo", None, [
            {"campo": "codigoRecorrido", "detalle": f"El recorrido {codigo} no tiene resultados calculados"}]
    return None


def procesar_correccion_recorrido(db: Session, codigo: str, distancia: float,
                                  consumo: float) -> tuple[ResultadoRecorrido, ResultadoRecorrido]:
    repositorio = RecorridoRepositorioSQLAlchemy(db)
    recorrido = repositorio.buscar(codigo)
    anterior = repositorio.resultado_vigente(codigo)
    nuevo = calcular_resultado(db, codigo, distancia, consumo, recorrido.id_tipo, recorrido.id_combustible,
                               recorrido.fecha_cierre, anterior.version + 1)
    repositorio.guardar_resultado(nuevo)
    return anterior, nuevo


def _recalcular_consumo(db: Session, codigo: str, distancia, consumo) -> tuple:
    errores = [e for e in [v.error_positivo("distanciaKm", distancia, "Debe ser mayor que 0"),
                           v.error_positivo("consumoRegistradoL", consumo, "Debe ser mayor que 0")] if e]
    if errores:
        return 422, "Los valores corregidos no son válidos", None, errores
    repositorio = RecorridoRepositorioSQLAlchemy(db)
    codigo = v.normalizar_codigo(codigo)
    rechazo = _sin_resultado_previo(codigo, repositorio.buscar(codigo), repositorio.resultado_vigente(codigo))
    if rechazo:
        return rechazo
    anterior, nuevo = procesar_correccion_recorrido(db, codigo, v.positivo(distancia), v.positivo(consumo))
    db.commit()
    return 200, "Consumo recalculado", {
        "codigoRecorrido": codigo, "version": nuevo.version, "factorConsumoLkm": nuevo.factor_consumo_lkm,
        "consumoEstimadoL": nuevo.consumo_estimado_l, "rendimientoLkm": nuevo.rendimiento_lkm,
        "desviacionPct": nuevo.desviacion_pct,
        "versionAnterior": {"version": anterior.version, "desviacionPct": anterior.desviacion_pct}}, []


def _contrato(db: Session, funcionalidad: str, mensaje_503: str, calculo, *argumentos) -> dict:
    try:
        return cuerpo_estandar(*calculo(db, *argumentos), funcionalidad)
    except SQLAlchemyError:
        db.rollback()
        return cuerpo_estandar(503, mensaje_503, None, ERROR_BD, funcionalidad)


def recalcular_consumo(db: Session, codigo: str, distancia, consumo) -> dict:
    return _contrato(db, "FUN-48", "No fue posible recalcular el consumo del recorrido", _recalcular_consumo,
                     codigo, distancia, consumo)
