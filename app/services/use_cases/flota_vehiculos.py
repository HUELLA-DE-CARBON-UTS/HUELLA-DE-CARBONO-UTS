from sqlalchemy.orm import Session

from app.domain.entities.vehiculo import FichaTecnica, Vehiculo
from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado, SolicitudIncorrecta
from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy
from app.services.contratos.ic02_consultar_catalogo_vigente import (
    consultar_catalogo_vigente, error_de_catalogo, nombre_en_catalogo, solo_falta_factor)
from app.services.contratos.ic11_consultar_sede import consultar_sede, error_de_sede, ids_de_sede, nombres_de_sedes
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import vehiculo_validador as v
from app.services.validators.catalogo_validador import limpiar


def _ficha_vigente(repositorio: VehiculoRepositorioSQLAlchemy, placa: str) -> FichaTecnica | None:
    fichas = repositorio.fichas(placa)
    dia = hoy()
    return next((f for f in fichas if f.aplica_en(dia)), fichas[-1] if fichas else None)


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
