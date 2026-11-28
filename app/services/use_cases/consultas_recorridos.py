from sqlalchemy.orm import Session

from app.domain.exceptions.errores import NoEncontrado
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic08_consultar_resultado_recorrido import consultar_resultado_recorrido
from app.services.use_cases.transaccion import transaccion
from app.services.validators import recorrido_validador as v

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
