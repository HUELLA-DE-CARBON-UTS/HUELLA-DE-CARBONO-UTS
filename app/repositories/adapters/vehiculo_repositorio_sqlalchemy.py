from sqlalchemy.orm import Session

from app.domain.entities.vehiculo import FichaTecnica, Vehiculo
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos_flota import FichaTecnicaModelo, VehiculoModelo


def _vehiculo(modelo: VehiculoModelo) -> Vehiculo:
    return Vehiculo(placa=modelo.placa, id_sede=modelo.id_sede, estado=modelo.estado)


def _ficha(modelo: FichaTecnicaModelo) -> FichaTecnica:
    return FichaTecnica(id_tipo=modelo.id_tipo, id_combustible=modelo.id_combustible, capacidad_t=modelo.capacidad_t,
                        vigente_desde=modelo.vigente_desde, vigente_hasta=modelo.vigente_hasta,
                        responsable=modelo.responsable, id=modelo.id)


class VehiculoRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def buscar(self, placa: str) -> Vehiculo | None:
        modelo = self.sesion.get(VehiculoModelo, placa)
        return _vehiculo(modelo) if modelo else None

    def guardar(self, vehiculo: Vehiculo, ficha: FichaTecnica) -> None:
        self.sesion.add(VehiculoModelo(placa=vehiculo.placa, id_sede=vehiculo.id_sede, estado=vehiculo.estado,
                                       fecha_registro=ahora(), responsable=ficha.responsable))
        self.sesion.flush()
        self.agregar_ficha(vehiculo.placa, ficha)

    def agregar_ficha(self, placa: str, ficha: FichaTecnica) -> None:
        self.sesion.add(FichaTecnicaModelo(placa=placa, id_tipo=ficha.id_tipo, id_combustible=ficha.id_combustible,
                                           capacidad_t=ficha.capacidad_t, vigente_desde=ficha.vigente_desde,
                                           vigente_hasta=None, responsable=ficha.responsable,
                                           fecha_registro=ahora()))
        self.sesion.flush()
