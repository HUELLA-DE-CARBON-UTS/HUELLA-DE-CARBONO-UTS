from sqlalchemy.orm import Session

from app.domain.entities.recorrido import Recorrido
from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic03_consultar_disponibilidad_vehiculo import (
    consultar_disponibilidad_vehiculo, detalle_no_disponible)
from app.services.contratos.ic04_cambiar_estado_operativo_vehiculo import cambiar_estado_operativo_vehiculo
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import recorrido_validador as v
from app.services.validators.catalogo_validador import fecha, limpiar
from app.services.validators.vehiculo_validador import normalizar_placa


def _vehiculo_no_encontrado(placa: str) -> NoEncontrado:
    return NoEncontrado("Vehículo no encontrado", [
        {"campo": "placa", "detalle": f"No existe un vehículo con la placa {placa}"}])


def _error_fecha_programada(valor) -> dict | None:
    error = v.error_fecha("fechaProgramada", valor)
    if error:
        return error
    if fecha(valor) < hoy():
        return {"campo": "fechaProgramada", "detalle": "La fecha no puede ser anterior a hoy (RN-05)"}
    return None


class ProgramarRecorrido:

    MENSAJE_503 = "No fue posible programar el recorrido"

    def __init__(self, db: Session, distancias):
        self.db = db
        self.distancias = distancias
        self.repositorio = RecorridoRepositorioSQLAlchemy(db)

    def ejecutar(self, placa, origen, destino, fecha_programada, responsable: str) -> dict:
        placa, origen, destino = normalizar_placa(placa), limpiar(origen), limpiar(destino)
        errores = [
            {"campo": "placa", "detalle": "La placa es obligatoria"} if not placa else v.error_placa(placa),
            None if origen else {"campo": "origen", "detalle": "El origen es obligatorio"},
            None if destino else {"campo": "destino", "detalle": "El destino es obligatorio"},
            {"campo": "destino", "detalle": "El destino debe ser distinto del origen (RN-05)"}
            if origen and destino and origen.lower() == destino.lower() else None,
            _error_fecha_programada(fecha_programada),
        ]
        errores = [e for e in errores if e]
        if errores:
            raise DatosNoValidos("Los datos del recorrido no son válidos", errores)

        with transaccion(self.db, self.MENSAJE_503):
            info = consultar_disponibilidad_vehiculo(self.db, placa)
            if not info["existe"]:
                raise _vehiculo_no_encontrado(placa)
            if info["estado"] != "disponible":
                raise Conflicto("El vehículo no está disponible", [
                    {"campo": "placa", "detalle": detalle_no_disponible(info)}])
            distancia = self.distancias.distancia_estimada_km(origen, destino)
            recorrido = Recorrido(codigo=self.repositorio.siguiente_codigo(), placa=placa, origen=origen,
                                  destino=destino, fecha_programada=fecha(fecha_programada),
                                  id_tipo=info["idTipo"], id_combustible=info["idCombustible"],
                                  distancia_estimada_km=distancia)
            self.repositorio.guardar(recorrido, responsable)
            cambiar_estado_operativo_vehiculo(self.db, placa, "asignado")
            self.db.commit()

        return {"codigoRecorrido": recorrido.codigo, "placa": placa, "origen": origen, "destino": destino,
                "fechaProgramada": recorrido.fecha_programada.isoformat(), "distanciaEstimadaKm": distancia,
                "estado": recorrido.estado}
