"""Creación de tablas y datos iniciales.

Registra el catálogo de operaciones (FUN-01 a FUN-65) y el rol
"Administrador" con todas ellas, para que exista quien configure los demás
roles (HU-11) antes de que se implemente el registro de usuarios (HU-01).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.value_objects.fecha import ahora
from app.domain.value_objects.operaciones import OPERACIONES
from app.repositories.config.settings import settings
from app.repositories.database import modelos  # noqa: F401  (registra las tablas)
from app.repositories.database.conexion import Base


def inicializar_base_de_datos(engine, sesion: Session) -> None:
    Base.metadata.create_all(bind=engine)

    existentes = set(sesion.scalars(select(modelos.OperacionModelo.codigo)))
    for codigo, nombre in OPERACIONES.items():
        if codigo not in existentes:
            sesion.add(modelos.OperacionModelo(codigo=codigo, nombre=nombre))
    sesion.flush()

    if sesion.scalar(select(modelos.RolModelo).where(modelos.RolModelo.nombre == "Administrador")) is None:
        sesion.add(modelos.RolModelo(
            id_rol="ROL-01",
            nombre="Administrador",
            descripcion="Administra usuarios, roles, sedes y catálogos del sistema",
            estado="activo",
            fecha_actualizacion=ahora(),
            responsable=settings.documento_admin_inicial,
            operaciones=list(sesion.scalars(select(modelos.OperacionModelo))),
        ))
    sesion.commit()
