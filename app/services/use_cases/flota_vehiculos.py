from sqlalchemy.orm import Session

from app.domain.entities.vehiculo import FichaTecnica, Vehiculo
from app.domain.exceptions.errores import Conflicto, DatosNoValidos
from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy
from app.services.contratos.ic02_consultar_catalogo_vigente import (
    consultar_catalogo_vigente, error_de_catalogo, solo_falta_factor)
from app.services.contratos.ic11_consultar_sede import consultar_sede, error_de_sede
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import vehiculo_validador as v
from app.services.validators.catalogo_validador import limpiar


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
