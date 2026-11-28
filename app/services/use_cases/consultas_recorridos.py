from sqlalchemy.orm import Session

from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic08_consultar_resultado_recorrido import consultar_resultado_recorrido
from app.services.contratos.ic16_consultar_vehiculos_por_criterio import placas_de_sede
from app.services.use_cases.transaccion import transaccion
from app.services.validators import recorrido_validador as v
from app.services.validators.catalogo_validador import limpiar

NO_APLICA = "no aplica"


class ConsultarRecorrido:

    MENSAJE_503 = "No fue posible consultar el recorrido"

    def __init__(self, db: Session):
        self.db = db

    def ejecutar(self, codigo) -> dict:
        codigo = v.validar_codigo(codigo)
        with transaccion(self.db, self.MENSAJE_503):
            recorrido = RecorridoRepositorioSQLAlchemy(self.db).buscar(codigo)
            if recorrido is None:
                raise NoEncontrado("Recorrido no encontrado", [
                    {"campo": "codigoRecorrido", "detalle": f"No existe el recorrido {codigo}"}])
            resultado = consultar_resultado_recorrido(self.db, codigo) if recorrido.estado == "cerrado" else None

        datos = {"codigoRecorrido": codigo, "placa": recorrido.placa, "origen": recorrido.origen,
                 "destino": recorrido.destino, "estado": recorrido.estado, "distanciaKm": recorrido.distancia_km,
                 "consumoRegistradoL": recorrido.consumo_registrado_l}
        if resultado is None:
            calculos = dict.fromkeys(("consumoEstimadoL", "desviacionPct", "emisionesKgCO2", "factorConsumoLkm",
                                      "factorEmisionKgCO2L"), NO_APLICA)
        else:
            calculos = {"consumoEstimadoL": resultado.consumo_estimado_l, "desviacionPct": resultado.desviacion_pct,
                        "emisionesKgCO2": resultado.emisiones_kgco2, "factorConsumoLkm": resultado.factor_consumo_lkm,
                        "factorEmisionKgCO2L": resultado.factor_emision_kgco2l}
        return {**datos, **calculos}


class ConsultarHistorialRecorridos:

    MENSAJE_503 = "No fue posible consultar el historial de recorridos"

    def __init__(self, db: Session):
        self.db = db

    def ejecutar(self, fecha_inicial, fecha_final, sede=None, estado=None) -> list[dict]:
        inicio, fin = v.rango_obligatorio(fecha_inicial, fecha_final)
        sede, estado = limpiar(sede), limpiar(estado).lower()
        if estado and estado not in v.ESTADOS:
            raise DatosNoValidos("Los parámetros de consulta no son válidos", [
                {"campo": "estado", "detalle": 'El estado debe ser "programado", "cerrado" o "cancelado"'}])

        with transaccion(self.db, self.MENSAJE_503):
            placas = placas_de_sede(self.db, sede) if sede else None
            recorridos = [r for r in RecorridoRepositorioSQLAlchemy(self.db).listar()
                          if v.en_rango(r.fecha_referencia(), inicio, fin)
                          and (not estado or r.estado == estado) and (placas is None or r.placa in placas)]
        if not recorridos:
            raise NoEncontrado("Sin resultados", [
                {"campo": "fechaInicial", "detalle": "No hay recorridos en el rango indicado"}])
        recorridos.sort(key=lambda r: (r.fecha_referencia(), r.codigo), reverse=True)
        return [{"codigoRecorrido": r.codigo, "placa": r.placa, "fecha": r.fecha_referencia().isoformat(),
                 "origen": r.origen, "destino": r.destino, "distanciaKm": r.distancia_km,
                 "litros": r.consumo_registrado_l, "estado": r.estado} for r in recorridos]
