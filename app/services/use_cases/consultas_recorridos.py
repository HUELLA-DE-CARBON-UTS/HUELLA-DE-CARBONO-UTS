from sqlalchemy.orm import Session

from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic03_consultar_disponibilidad_vehiculo import consultar_disponibilidad_vehiculo
from app.services.contratos.ic08_consultar_resultado_recorrido import consultar_resultado_recorrido
from app.services.contratos.ic16_consultar_vehiculos_por_criterio import placas_de_sede
from app.services.contratos.ic19_consultar_datos_recorridos import consultar_datos_recorridos
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import recorrido_validador as v
from app.services.validators.catalogo_validador import limpiar
from app.services.validators.vehiculo_validador import normalizar_placa

NO_APLICA = "no aplica"


def _validar_placa(placa) -> str:
    placa = normalizar_placa(placa)
    error = v.error_placa(placa)
    if error:
        raise DatosNoValidos("Los parámetros de consulta no son válidos", [error])
    return placa


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


class ConsultarPendientesCierre:

    MENSAJE_503 = "No fue posible consultar los recorridos pendientes de cierre"

    def __init__(self, db: Session):
        self.db = db

    def ejecutar(self, sede=None, placa=None) -> list[dict]:
        sede, placa = limpiar(sede), _validar_placa(placa)
        with transaccion(self.db, self.MENSAJE_503):
            dia = hoy()
            placas = placas_de_sede(self.db, sede) if sede else None
            vencidos = [r for r in RecorridoRepositorioSQLAlchemy(self.db).listar()
                        if r.estado == "programado" and r.fecha_programada < dia
                        and (not placa or r.placa == placa) and (placas is None or r.placa in placas)]
        if not vencidos:
            if sede:
                error = {"campo": "sede", "detalle": f"No hay recorridos vencidos en la sede {sede}"}
            elif placa:
                error = {"campo": "placa", "detalle": f"No hay recorridos vencidos del vehículo {placa}"}
            else:
                error = {"campo": "criterios", "detalle": "No hay recorridos programados con fecha vencida"}
            raise NoEncontrado("Sin recorridos pendientes de cierre", [error])
        vencidos.sort(key=lambda r: (r.fecha_programada, r.codigo))
        return [{"codigoRecorrido": r.codigo, "placa": r.placa, "fechaProgramada": r.fecha_programada.isoformat(),
                 "diasAtraso": (dia - r.fecha_programada).days} for r in vencidos]


class ConsultarRecorridosVehiculo:

    MENSAJE_503 = "No fue posible consultar los recorridos del vehículo"

    def __init__(self, db: Session):
        self.db = db

    def ejecutar(self, placa, fecha_inicial, fecha_final) -> dict:
        placa = normalizar_placa(placa)
        inicio, fin = v.rango_obligatorio(fecha_inicial, fecha_final)
        with transaccion(self.db, self.MENSAJE_503):
            if not consultar_disponibilidad_vehiculo(self.db, placa)["existe"]:
                raise NoEncontrado("Vehículo no encontrado", [
                    {"campo": "placa", "detalle": f"No existe un vehículo con la placa {placa}"}])
            recorridos = consultar_datos_recorridos(self.db, inicio, fin, placa=placa)
        recorridos.sort(key=lambda r: (r.fecha_cierre, r.codigo), reverse=True)
        return {"placa": placa,
                "recorridos": [{"codigoRecorrido": r.codigo, "fecha": r.fecha_cierre.isoformat(),
                                "distanciaKm": r.distancia_km, "litros": r.consumo_registrado_l} for r in recorridos],
                "totalRecorridos": len(recorridos),
                "distanciaTotalKm": round(sum(r.distancia_km for r in recorridos), 2)}
