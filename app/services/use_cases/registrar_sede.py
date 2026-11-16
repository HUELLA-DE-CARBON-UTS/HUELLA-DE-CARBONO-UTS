"""Caso de uso FUN-16 / PRO-16: registrar una nueva sede."""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.domain.entities.sede import Sede
from app.domain.exceptions.errores import Conflicto, ServicioNoDisponible
from app.domain.interfaces.sede_repositorio import SedeRepositorio
from app.domain.value_objects.fecha import ahora
from app.services.validators import sede_validador


def _sede_duplicada(nombre: str, ciudad: str) -> Conflicto:
    return Conflicto("Ya existe una sede con ese nombre en la ciudad", [
        {"campo": "nombre", "detalle": f"La sede {nombre} ya está registrada en {ciudad}"},
    ])


class RegistrarSede:
    def __init__(self, repositorio: SedeRepositorio):
        self.repositorio = repositorio

    def ejecutar(self, nombre: str, ciudad: str, direccion: str, responsable: str) -> Sede:
        datos = {
            "nombre": sede_validador.limpiar(nombre),
            "ciudad": sede_validador.limpiar(ciudad),
            "direccion": sede_validador.limpiar(direccion),
            "responsable": sede_validador.limpiar(responsable),
        }
        sede_validador.validar_obligatorios(datos)

        try:
            if self.repositorio.existe_en_ciudad(datos["nombre"], datos["ciudad"]):
                raise _sede_duplicada(datos["nombre"], datos["ciudad"])
            sede = Sede(
                id_sede=self.repositorio.siguiente_id(),
                estado="activa",
                fecha_creacion=ahora(),
                **datos,
            )
            return self.repositorio.guardar(sede)
        except IntegrityError as exc:
            # Otra solicitud registró la misma sede entre la verificación y el guardado.
            raise _sede_duplicada(datos["nombre"], datos["ciudad"]) from exc
        except SQLAlchemyError as exc:
            raise ServicioNoDisponible(
                "No fue posible registrar la sede",
                [{"campo": "baseDeDatos", "detalle": "La base de datos no está disponible"}],
            ) from exc
