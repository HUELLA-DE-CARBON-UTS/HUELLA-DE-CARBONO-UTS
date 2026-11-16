"""Implementación del repositorio de sedes con SQLAlchemy."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.sede import Sede
from app.repositories.database.modelos import SedeModelo


def _a_entidad(modelo: SedeModelo) -> Sede:
    return Sede(
        id_sede=modelo.id_sede,
        nombre=modelo.nombre,
        ciudad=modelo.ciudad,
        direccion=modelo.direccion,
        responsable=modelo.responsable,
        estado=modelo.estado,
        fecha_creacion=modelo.fecha_creacion,
    )


class SedeRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def existe_en_ciudad(self, nombre: str, ciudad: str) -> bool:
        consulta = select(SedeModelo.id_sede).where(
            func.lower(SedeModelo.nombre) == nombre.lower(),
            func.lower(SedeModelo.ciudad) == ciudad.lower(),
        )
        return self.sesion.scalar(consulta) is not None

    def buscar_por_id(self, id_sede: str) -> Sede | None:
        modelo = self.sesion.get(SedeModelo, id_sede)
        return _a_entidad(modelo) if modelo else None

    def buscar_por_nombre(self, nombre: str) -> list[Sede]:
        consulta = select(SedeModelo).where(func.lower(SedeModelo.nombre) == nombre.lower())
        return [_a_entidad(m) for m in self.sesion.scalars(consulta)]

    def siguiente_id(self) -> str:
        ids = self.sesion.scalars(select(SedeModelo.id_sede)).all()
        mayor = max((int(i.split("-")[1]) for i in ids), default=0)
        return f"SED-{mayor + 1:02d}"

    def guardar(self, sede: Sede) -> Sede:
        modelo = SedeModelo(
            id_sede=sede.id_sede,
            nombre=sede.nombre,
            ciudad=sede.ciudad,
            direccion=sede.direccion,
            responsable=sede.responsable,
            estado=sede.estado,
            fecha_creacion=sede.fecha_creacion,
        )
        self.sesion.add(modelo)
        self.sesion.commit()
        return _a_entidad(modelo)
