from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.catalogo import ElementoCatalogo, Factor
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos_catalogo import FactorConsumoModelo, TipoVehiculoModelo


@dataclass(frozen=True)
class Configuracion:
    modelo: type
    columna_id: str
    modelo_factor: type
    prefijo: str
    con_fuente: bool


TIPOS_VEHICULO = Configuracion(TipoVehiculoModelo, "id_tipo", FactorConsumoModelo, "TV", False)


class CatalogoRepositorioSQLAlchemy:
    def __init__(self, sesion: Session, configuracion: Configuracion):
        self.sesion = sesion
        self.c = configuracion

    def _id(self, modelo):
        return getattr(modelo, self.c.columna_id)

    def _elemento(self, modelo) -> ElementoCatalogo:
        return ElementoCatalogo(id=self._id(modelo), nombre=modelo.nombre, descripcion=modelo.descripcion,
                                estado=modelo.estado)

    def buscar_por_nombre(self, nombre: str) -> ElementoCatalogo | None:
        modelo = self.sesion.scalar(select(self.c.modelo).where(func.lower(self.c.modelo.nombre) == nombre.lower()))
        return self._elemento(modelo) if modelo else None

    def siguiente_id(self) -> str:
        ids = self.sesion.scalars(select(getattr(self.c.modelo, self.c.columna_id))).all()
        mayor = max((int(i.split("-")[1]) for i in ids), default=0)
        return f"{self.c.prefijo}-{mayor + 1:02d}"

    def guardar(self, elemento: ElementoCatalogo, factor: Factor) -> None:
        self.sesion.add(self.c.modelo(**{self.c.columna_id: elemento.id}, nombre=elemento.nombre,
                                      descripcion=elemento.descripcion, estado=elemento.estado,
                                      fecha_creacion=ahora(), responsable=factor.responsable))
        self.sesion.flush()
        self.agregar_factor(elemento.id, factor)

    def agregar_factor(self, identificador: str, factor: Factor) -> None:
        datos = {self.c.columna_id: identificador, "valor": factor.valor, "vigente_desde": factor.vigente_desde,
                 "vigente_hasta": None, "responsable": factor.responsable, "fecha_registro": ahora()}
        if self.c.con_fuente:
            datos["fuente"] = factor.fuente or ""
        self.sesion.add(self.c.modelo_factor(**datos))
        self.sesion.flush()
