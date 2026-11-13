"""Implementación del repositorio de roles con SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.rol import Rol
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos import OperacionModelo, RolModelo


def _a_entidad(modelo: RolModelo) -> Rol:
    return Rol(
        id_rol=modelo.id_rol,
        nombre=modelo.nombre,
        descripcion=modelo.descripcion,
        estado=modelo.estado,
        permisos=sorted(o.codigo for o in modelo.operaciones),
    )


class RolRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def buscar_por_nombre(self, nombre: str) -> Rol | None:
        modelo = self.sesion.scalar(select(RolModelo).where(RolModelo.nombre == nombre))
        return _a_entidad(modelo) if modelo else None

    def operaciones_existentes(self, codigos: list[str]) -> set[str]:
        consulta = select(OperacionModelo.codigo).where(OperacionModelo.codigo.in_(codigos))
        return set(self.sesion.scalars(consulta))

    def siguiente_id(self) -> str:
        ids = self.sesion.scalars(select(RolModelo.id_rol)).all()
        mayor = max((int(i.split("-")[1]) for i in ids), default=0)
        return f"ROL-{mayor + 1:02d}"

    def guardar(self, rol: Rol, responsable: str) -> Rol:
        modelo = self.sesion.scalar(select(RolModelo).where(RolModelo.nombre == rol.nombre))
        if modelo is None:
            modelo = RolModelo(id_rol=rol.id_rol, nombre=rol.nombre, estado=rol.estado)
            self.sesion.add(modelo)
        modelo.descripcion = rol.descripcion
        modelo.operaciones = list(
            self.sesion.scalars(select(OperacionModelo).where(OperacionModelo.codigo.in_(rol.permisos)))
        )
        modelo.fecha_actualizacion = ahora()
        modelo.responsable = responsable
        self.sesion.commit()
        return _a_entidad(modelo)
