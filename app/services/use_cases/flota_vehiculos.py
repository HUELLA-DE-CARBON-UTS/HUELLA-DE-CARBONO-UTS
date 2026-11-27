from datetime import timedelta

from sqlalchemy.orm import Session

from app.domain.entities.vehiculo import FichaTecnica, Vehiculo
from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado, SolicitudIncorrecta
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy
from app.services.contratos.ic02_consultar_catalogo_vigente import (
    consultar_catalogo_vigente, error_de_catalogo, nombre_en_catalogo, solo_falta_factor)
from app.services.contratos.ic11_consultar_sede import consultar_sede, error_de_sede, ids_de_sede, nombres_de_sedes
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import vehiculo_validador as v
from app.services.validators.catalogo_validador import fecha, limpiar


def _no_encontrado(placa: str) -> NoEncontrado:
    return NoEncontrado("Vehículo no encontrado", [
        {"campo": "placa", "detalle": f"No existe un vehículo con la placa {placa}"}])


def _asignado(placa: str) -> Conflicto:
    return Conflicto("El vehículo está asignado a un recorrido abierto", [
        {"campo": "placa", "detalle": f"El vehículo {placa} está asignado a un recorrido abierto"}])


def _ficha_vigente(repositorio: VehiculoRepositorioSQLAlchemy, placa: str) -> FichaTecnica | None:
    fichas = repositorio.fichas(placa)
    dia = hoy()
    return next((f for f in fichas if f.aplica_en(dia)), fichas[-1] if fichas else None)


def _buscar_disponible_para_cambios(repositorio: VehiculoRepositorioSQLAlchemy, placa: str) -> Vehiculo:
    vehiculo = repositorio.buscar(placa)
    if vehiculo is None:
        raise _no_encontrado(placa)
    if vehiculo.estado == "asignado":
        raise _asignado(placa)
    return vehiculo


class RegistrarVehiculo:

    MENSAJE_503 = "No fue posible registrar el vehículo"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = VehiculoRepositorioSQLAlchemy(db)

    def ejecutar(self, placa, tipo, combustible, capacidad, sede, responsable: str) -> dict:
        placa, tipo, combustible, sede = v.normalizar_placa(placa), limpiar(tipo), limpiar(combustible), limpiar(sede)
        errores = [e for e in [
            v.error_placa(placa),
            v.error_obligatorio("tipoVehiculo", tipo, "El tipo de vehículo es obligatorio"),
            v.error_obligatorio("combustible", combustible, "El combustible es obligatorio"),
            v.error_capacidad(capacidad),
            v.error_obligatorio("sede", sede, "La sede es obligatoria"),
        ] if e]
        if errores:
            raise DatosNoValidos("Los datos del vehículo no son válidos", errores)

        duplicado = Conflicto("La placa ya está registrada", [
            {"campo": "placa", "detalle": f"Ya existe un vehículo con la placa {placa}"}])
        with transaccion(self.db, self.MENSAJE_503, duplicado):
            if self.repositorio.buscar(placa) is not None:
                raise duplicado

            info_tipo = consultar_catalogo_vigente(self.db, "tipo", tipo)
            info_combustible = consultar_catalogo_vigente(self.db, "combustible", combustible)
            errores = [e for e in [error_de_catalogo(info_tipo, "tipo", tipo, "tipoVehiculo"),
                                   error_de_catalogo(info_combustible, "combustible", combustible, "combustible")] if e]
            if errores:
                mensaje = "El tipo de vehículo o el combustible no tienen factor vigente" if solo_falta_factor(errores) \
                    else "El tipo de vehículo o el combustible no son válidos"
                raise DatosNoValidos(mensaje, errores)

            info_sede = consultar_sede(self.db, sede)
            error = error_de_sede(info_sede, sede, "sede")
            if error:
                raise DatosNoValidos("La sede indicada no está disponible", [error])

            vehiculo = Vehiculo(placa=placa, id_sede=info_sede["idSede"])
            ficha = FichaTecnica(id_tipo=info_tipo["id"], id_combustible=info_combustible["id"],
                                 capacidad_t=v.capacidad(capacidad), vigente_desde=hoy(), responsable=responsable)
            self.repositorio.guardar(vehiculo, ficha)
            self.db.commit()

        return {"placa": placa, "tipoVehiculo": info_tipo["nombre"], "combustible": info_combustible["nombre"],
                "capacidadT": ficha.capacidad_t, "sede": info_sede["nombre"], "estado": v.estado_api(vehiculo.estado)}


class ConsultarVehiculos:

    MENSAJE_503 = "No fue posible consultar los vehículos"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = VehiculoRepositorioSQLAlchemy(db)

    def ejecutar(self, placa=None, tipo=None, sede=None, estado=None) -> list[dict]:
        placa, tipo, sede, estado = v.normalizar_placa(placa), limpiar(tipo), limpiar(sede), limpiar(estado).lower()
        if not any([placa, tipo, sede, estado]):
            raise SolicitudIncorrecta("Debe indicar al menos un criterio de búsqueda", [
                {"campo": "criterios", "detalle": "No se recibió placa, tipo, sede ni estado"}])
        if estado and v.error_estado_busqueda(estado):
            raise DatosNoValidos("Los criterios de búsqueda no son válidos", [v.error_estado_busqueda(estado)])

        with transaccion(self.db, self.MENSAJE_503):
            sedes_validas = set(ids_de_sede(self.db, sede)) if sede else None
            estado_interno = v.ESTADOS_INTERNOS.get(estado) if estado else None
            nombres_tipo, nombres_combustible = {}, {}
            resultado = []
            for vehiculo in self.repositorio.listar():
                if placa and placa not in vehiculo.placa:
                    continue
                if sedes_validas is not None and vehiculo.id_sede not in sedes_validas:
                    continue
                if estado_interno and vehiculo.estado != estado_interno:
                    continue
                ficha = _ficha_vigente(self.repositorio, vehiculo.placa)
                if ficha.id_tipo not in nombres_tipo:
                    nombres_tipo[ficha.id_tipo] = nombre_en_catalogo(self.db, "tipo", ficha.id_tipo)
                nombre_tipo = nombres_tipo[ficha.id_tipo]
                if tipo and tipo.upper() != ficha.id_tipo and tipo.lower() != nombre_tipo.lower():
                    continue
                if ficha.id_combustible not in nombres_combustible:
                    nombres_combustible[ficha.id_combustible] = nombre_en_catalogo(
                        self.db, "combustible", ficha.id_combustible)
                resultado.append((vehiculo, nombre_tipo, nombres_combustible[ficha.id_combustible]))

            if not resultado:
                raise NoEncontrado("Sin resultados", [
                    {"campo": "criterios", "detalle": "No hay vehículos que cumplan los criterios"}])
            sedes = nombres_de_sedes(self.db, [r[0].id_sede for r in resultado])
            return [{"placa": vehiculo.placa, "tipo": nombre_tipo, "combustible": nombre_combustible,
                     "sede": sedes.get(vehiculo.id_sede, vehiculo.id_sede), "estado": v.estado_api(vehiculo.estado)}
                    for vehiculo, nombre_tipo, nombre_combustible in resultado]


class ActualizarFichaTecnica:

    MENSAJE_503 = "No fue posible actualizar la ficha técnica"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = VehiculoRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, placa, tipo, combustible, capacidad, aplica_desde, responsable: str) -> dict:
        placa, tipo, combustible = v.normalizar_placa(placa), limpiar(tipo), limpiar(combustible)
        desde = fecha(aplica_desde)
        errores = []
        if not tipo and not combustible and capacidad is None:
            errores.append({"campo": "datos", "detalle": "Debe indicar el tipo de vehículo, el combustible o la capacidad"})
        if capacidad is not None:
            errores.append(v.error_capacidad(capacidad))
        if desde is None:
            errores.append({"campo": "aplicaDesde",
                            "detalle": "La fecha desde la que aplica es obligatoria y debe tener el formato AAAA-MM-DD"})
        errores = [e for e in errores if e]
        if errores:
            raise DatosNoValidos("Los datos de la ficha técnica no son válidos", errores)

        with transaccion(self.db, self.MENSAJE_503):
            _buscar_disponible_para_cambios(self.repositorio, placa)
            actual = self.repositorio.ficha_abierta(placa)

            errores, nuevos = [], {}
            for catalogo, referencia, campo in (("tipo", tipo, "tipoVehiculo"), ("combustible", combustible, "combustible")):
                if referencia:
                    info = consultar_catalogo_vigente(self.db, catalogo, referencia)
                    error = error_de_catalogo(info, catalogo, referencia, campo)
                    if error:
                        errores.append(error)
                    else:
                        nuevos[catalogo] = info
            if errores:
                raise DatosNoValidos("El nuevo tipo o combustible no es válido", errores)

            nueva = FichaTecnica(
                id_tipo=nuevos["tipo"]["id"] if "tipo" in nuevos else actual.id_tipo,
                id_combustible=nuevos["combustible"]["id"] if "combustible" in nuevos else actual.id_combustible,
                capacidad_t=v.capacidad(capacidad) if capacidad is not None else actual.capacidad_t,
                vigente_desde=desde, responsable=responsable, id=actual.id)

            cambios = []
            if nueva.id_tipo != actual.id_tipo:
                cambios.append({"campo": "tipoVehiculo", "valorAnterior": nombre_en_catalogo(self.db, "tipo", actual.id_tipo),
                                "valorNuevo": nuevos["tipo"]["nombre"]})
            if nueva.id_combustible != actual.id_combustible:
                cambios.append({"campo": "combustible",
                                "valorAnterior": nombre_en_catalogo(self.db, "combustible", actual.id_combustible),
                                "valorNuevo": nuevos["combustible"]["nombre"]})
            if nueva.capacidad_t != actual.capacidad_t:
                cambios.append({"campo": "capacidadT", "valorAnterior": actual.capacidad_t,
                                "valorNuevo": nueva.capacidad_t})
            if not cambios:
                raise DatosNoValidos("No hay cambios en la ficha técnica", [
                    {"campo": "datos", "detalle": "Los valores enviados son iguales a los de la ficha vigente"}])

            inicio = actual.vigente_desde
            if desde < inicio:
                raise DatosNoValidos("La fecha desde la que aplica no es válida", [
                    {"campo": "aplicaDesde",
                     "detalle": f"No puede ser anterior al inicio de la ficha vigente ({inicio.isoformat()})"}])
            if desde == inicio:
                self.repositorio.reemplazar_ficha(nueva)
            else:
                self.repositorio.cerrar_ficha(actual, desde - timedelta(days=1))
                self.repositorio.agregar_ficha(placa, nueva)

            for cambio in cambios:
                self.historial.registrar("vehiculo", placa, f"ficha_tecnica_{cambio['campo']}",
                                         str(cambio["valorAnterior"]), str(cambio["valorNuevo"]), responsable,
                                         f"Aplica desde {desde.isoformat()}")
            self.db.commit()

        return {"placa": placa, "cambios": cambios, "aplicaDesde": desde.isoformat()}


class ActualizarEstadoSedeVehiculo:

    MENSAJE_503 = "No fue posible actualizar el vehículo"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = VehiculoRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, placa, estado, sede, responsable: str) -> dict:
        placa, estado, sede = v.normalizar_placa(placa), limpiar(estado).lower(), limpiar(sede)
        if not estado and not sede:
            raise DatosNoValidos("Los datos del vehículo no son válidos", [
                {"campo": "datos", "detalle": "Debe indicar el nuevo estado o la nueva sede"}])
        if estado and v.error_estado_manual(estado):
            raise DatosNoValidos("Los datos del vehículo no son válidos", [v.error_estado_manual(estado)])

        with transaccion(self.db, self.MENSAJE_503):
            vehiculo = _buscar_disponible_para_cambios(self.repositorio, placa)
            estado_anterior, sede_anterior = vehiculo.estado, vehiculo.id_sede

            if sede:
                info = consultar_sede(self.db, sede)
                error = error_de_sede(info, sede, "sede")
                if error and (not info["existe"] or info.get("ambigua")):
                    raise DatosNoValidos("La sede de destino no es válida", [error])
                if error or info["idSede"] == vehiculo.id_sede:
                    raise DatosNoValidos("La sede de destino no es válida", [
                        {"campo": "sede", "detalle": "La sede de destino debe estar activa y ser distinta de la actual"}])
                vehiculo.id_sede = info["idSede"]
            if estado:
                vehiculo.estado = v.ESTADOS_INTERNOS[estado]
            if vehiculo.estado == estado_anterior and vehiculo.id_sede == sede_anterior:
                raise DatosNoValidos("No hay cambios para aplicar", [
                    {"campo": "estado", "detalle": f"El vehículo ya se encuentra en estado {estado}"}])

            self.repositorio.actualizar(vehiculo)
            if vehiculo.estado != estado_anterior:
                self.historial.registrar("vehiculo", placa, "estado", estado_anterior, vehiculo.estado, responsable)
            if vehiculo.id_sede != sede_anterior:
                self.historial.registrar("vehiculo", placa, "sede", sede_anterior, vehiculo.id_sede, responsable)
            self.db.commit()

        sedes = nombres_de_sedes(self.db, [sede_anterior, vehiculo.id_sede])
        return {"placa": placa, "estadoAnterior": v.estado_api(estado_anterior),
                "estadoNuevo": v.estado_api(vehiculo.estado), "sedeAnterior": sedes.get(sede_anterior, sede_anterior),
                "sedeNueva": sedes.get(vehiculo.id_sede, vehiculo.id_sede)}
