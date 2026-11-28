from sqlalchemy.orm import Session

from app.domain.entities.recorrido import Recorrido
from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic03_consultar_disponibilidad_vehiculo import (
    consultar_disponibilidad_vehiculo, detalle_no_disponible)
from app.services.contratos.ic04_cambiar_estado_operativo_vehiculo import cambiar_estado_operativo_vehiculo
from app.services.contratos.ic05_procesar_cierre_recorrido import procesar_cierre_recorrido, resumen
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import recorrido_validador as v
from app.services.validators.catalogo_validador import fecha, limpiar
from app.services.validators.vehiculo_validador import normalizar_placa


def _no_encontrado(codigo: str) -> NoEncontrado:
    return NoEncontrado("Recorrido no encontrado", [
        {"campo": "codigoRecorrido", "detalle": f"No existe el recorrido {codigo}"}])


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


class ReprogramarRecorrido:

    MENSAJE_503 = "No fue posible reprogramar el recorrido"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = RecorridoRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, codigo, fecha_programada, placa, responsable: str) -> dict:
        codigo, placa = v.normalizar_codigo(codigo), normalizar_placa(placa)
        errores = []
        if not limpiar(fecha_programada) and not placa:
            errores.append({"campo": "datos", "detalle": "Debe indicar la nueva fecha o la nueva placa"})
        if limpiar(fecha_programada):
            errores.append(_error_fecha_programada(fecha_programada))
        errores.append(v.error_placa(placa))
        errores = [e for e in errores if e]
        if errores:
            raise DatosNoValidos("Los datos de la reprogramación no son válidos", errores)

        with transaccion(self.db, self.MENSAJE_503):
            recorrido = self.repositorio.buscar(codigo)
            if recorrido is None:
                raise _no_encontrado(codigo)
            if recorrido.estado != "programado":
                raise Conflicto("El recorrido no se puede reprogramar", [
                    {"campo": "codigoRecorrido", "detalle": f"El recorrido {codigo} ya está {recorrido.estado}"}])

            placa_anterior, fecha_anterior = recorrido.placa, recorrido.fecha_programada
            if placa and placa != recorrido.placa:
                info = consultar_disponibilidad_vehiculo(self.db, placa)
                if not info["existe"]:
                    raise _vehiculo_no_encontrado(placa)
                if info["estado"] != "disponible":
                    detalle = f"El vehículo {placa} está asignado a otro recorrido" \
                        if info["estado"] == "asignado" else detalle_no_disponible(info)
                    raise Conflicto("El nuevo vehículo no está disponible", [{"campo": "placa", "detalle": detalle}])
                cambiar_estado_operativo_vehiculo(self.db, placa_anterior, "disponible")
                cambiar_estado_operativo_vehiculo(self.db, placa, "asignado")
                recorrido.placa, recorrido.id_tipo, recorrido.id_combustible = \
                    placa, info["idTipo"], info["idCombustible"]
                self.historial.registrar("recorrido", codigo, "placa", placa_anterior, placa, responsable)
            if limpiar(fecha_programada):
                recorrido.fecha_programada = fecha(fecha_programada)
                if recorrido.fecha_programada != fecha_anterior:
                    self.historial.registrar("recorrido", codigo, "fecha_programada", fecha_anterior.isoformat(),
                                             recorrido.fecha_programada.isoformat(), responsable)
            self.repositorio.actualizar(recorrido)
            self.db.commit()

        return {"codigoRecorrido": codigo, "placaAnterior": placa_anterior, "placaNueva": recorrido.placa,
                "fechaProgramada": recorrido.fecha_programada.isoformat()}


class CancelarRecorrido:

    MENSAJE_503 = "No fue posible cancelar el recorrido"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = RecorridoRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, codigo, motivo, responsable: str) -> dict:
        codigo, motivo = v.normalizar_codigo(codigo), limpiar(motivo)
        if not motivo:
            raise DatosNoValidos("Los datos de la cancelación no son válidos", [
                {"campo": "motivo", "detalle": "El motivo es obligatorio"}])

        with transaccion(self.db, self.MENSAJE_503):
            recorrido = self.repositorio.buscar(codigo)
            if recorrido is None:
                raise _no_encontrado(codigo)
            if recorrido.estado != "programado":
                raise Conflicto("El recorrido no se puede cancelar", [
                    {"campo": "codigoRecorrido", "detalle": f"El recorrido {codigo} ya está {recorrido.estado}"}])
            recorrido.estado, recorrido.motivo_cancelacion = "cancelado", motivo
            self.repositorio.actualizar(recorrido)
            cambiar_estado_operativo_vehiculo(self.db, recorrido.placa, "disponible")
            self.historial.registrar("recorrido", codigo, "estado", "programado", "cancelado", responsable, motivo)
            self.db.commit()

        return {"codigoRecorrido": codigo, "estado": recorrido.estado, "motivo": motivo,
                "placaLiberada": recorrido.placa}


class CerrarRecorrido:

    MENSAJE_503 = "No fue posible registrar el cierre del recorrido"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = RecorridoRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, codigo, fecha_cierre, distancia, consumo, responsable: str) -> dict:
        codigo = v.normalizar_codigo(codigo)
        errores = [e for e in [v.error_fecha("fechaCierre", fecha_cierre),
                               v.error_positivo("distanciaKm", distancia),
                               v.error_positivo("consumoRegistradoL", consumo)] if e]
        if errores:
            raise DatosNoValidos("Los datos del cierre no son válidos", errores)

        with transaccion(self.db, self.MENSAJE_503):
            recorrido = self.repositorio.buscar(codigo)
            if recorrido is None:
                raise _no_encontrado(codigo)
            if recorrido.estado != "programado":
                raise Conflicto("El recorrido no se puede cerrar en su estado actual", [
                    {"campo": "codigoRecorrido",
                     "detalle": f'El recorrido {codigo} está en estado "{recorrido.estado}"'}])
            dia = fecha(fecha_cierre)
            if dia < recorrido.fecha_programada:
                raise DatosNoValidos("Los datos del cierre no son válidos", [
                    {"campo": "fechaCierre", "detalle": "La fecha de cierre no puede ser anterior a la fecha "
                                                       f"programada ({recorrido.fecha_programada.isoformat()})"}])
            recorrido.estado, recorrido.fecha_cierre = "cerrado", dia
            recorrido.distancia_km, recorrido.consumo_registrado_l = v.positivo(distancia), v.positivo(consumo)
            self.repositorio.actualizar(recorrido)
            resultado = procesar_cierre_recorrido(self.db, codigo, recorrido.distancia_km,
                                                  recorrido.consumo_registrado_l, recorrido.id_tipo,
                                                  recorrido.id_combustible, dia)
            cambiar_estado_operativo_vehiculo(self.db, recorrido.placa, "disponible")
            self.historial.registrar("recorrido", codigo, "estado", "programado", "cerrado", responsable)
            self.db.commit()

        return {"codigoRecorrido": codigo, "placa": recorrido.placa, "distanciaKm": recorrido.distancia_km,
                "consumoRegistradoL": recorrido.consumo_registrado_l, **resumen(resultado)}
