from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.exceptions.errores import NoEncontrado, SolicitudIncorrecta
from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy
from app.repositories.database.modelos import HistorialCambioModelo
from app.services.contratos.ic02_consultar_catalogo_vigente import nombre_en_catalogo
from app.services.contratos.ic11_consultar_sede import nombres_de_sedes
from app.services.contratos.ic17_consultar_actividad_vehiculo import consultar_actividad_vehiculo
from app.services.use_cases.catalogo_comun import hoy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import vehiculo_validador as v

TIPOS_EVENTO = {"estado": "estado", "sede": "sede", "ficha_tecnica_tipoVehiculo": "tipoVehiculo",
                "ficha_tecnica_combustible": "combustible", "ficha_tecnica_capacidadT": "capacidadT"}


class ConsultarHojaVidaVehiculo:

    MENSAJE_503 = "No fue posible consultar la hoja de vida del vehículo"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = VehiculoRepositorioSQLAlchemy(db)

    def ejecutar(self, placa) -> dict:
        placa = v.normalizar_placa(placa)
        if not v.FORMATO_PLACA.match(placa):
            raise SolicitudIncorrecta("La placa no es válida", [
                {"campo": "placa", "detalle": "La placa debe tener el formato AAA-000"}])

        with transaccion(self.db, self.MENSAJE_503):
            vehiculo = self.repositorio.buscar(placa)
            if vehiculo is None:
                raise NoEncontrado("Vehículo no encontrado", [
                    {"campo": "placa", "detalle": f"No existe un vehículo con la placa {placa}"}])
            fichas = self.repositorio.fichas(placa)
            dia = hoy()
            ficha = next((f for f in fichas if f.aplica_en(dia)), fichas[-1])
            cambios = self.db.scalars(select(HistorialCambioModelo).where(
                HistorialCambioModelo.entidad == "vehiculo", HistorialCambioModelo.id_entidad == placa)
                .order_by(HistorialCambioModelo.fecha.desc(), HistorialCambioModelo.id.desc())).all()
            sedes = nombres_de_sedes(self.db, [vehiculo.id_sede] + [
                valor for c in cambios if c.tipo_cambio == "sede" for valor in (c.valor_anterior, c.valor_nuevo)])
            actividad = consultar_actividad_vehiculo(self.db, placa)
            nombre_tipo = nombre_en_catalogo(self.db, "tipo", ficha.id_tipo)
            nombre_combustible = nombre_en_catalogo(self.db, "combustible", ficha.id_combustible)

        eventos = []
        for cambio in cambios:
            tipo = TIPOS_EVENTO.get(cambio.tipo_cambio, cambio.tipo_cambio)
            anterior, nuevo = cambio.valor_anterior, cambio.valor_nuevo
            if tipo == "estado":
                anterior, nuevo = v.estado_api(anterior), v.estado_api(nuevo)
            if tipo == "sede":
                anterior, nuevo = sedes.get(anterior, anterior), sedes.get(nuevo, nuevo)
            eventos.append({"fecha": cambio.fecha.date().isoformat(), "tipo": tipo, "valorAnterior": anterior,
                            "valorNuevo": nuevo, "responsable": cambio.responsable})

        return {
            "placa": placa,
            "fichaActual": {"tipo": nombre_tipo, "combustible": nombre_combustible,
                            "capacidadT": ficha.capacidad_t, "sede": sedes.get(vehiculo.id_sede, vehiculo.id_sede),
                            "estado": v.estado_api(vehiculo.estado)},
            "eventos": eventos,
            **actividad,
        }
