from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.value_objects.fecha import ahora
from app.domain.value_objects.operaciones import OPERACIONES
from app.repositories.config.settings import settings
from app.repositories.database import modelos
from app.repositories.database.conexion import Base
from app.services.seguridad.contrasenas import generar_hash


def inicializar_base_de_datos(engine, sesion: Session) -> None:
    Base.metadata.create_all(bind=engine)

    existentes = set(sesion.scalars(select(modelos.OperacionModelo.codigo)))
    for codigo, nombre in OPERACIONES.items():
        if codigo not in existentes:
            sesion.add(modelos.OperacionModelo(codigo=codigo, nombre=nombre))
    sesion.flush()

    administrador = sesion.scalar(select(modelos.RolModelo).where(modelos.RolModelo.nombre == "Administrador"))
    if administrador is None:
        administrador = modelos.RolModelo(
            id_rol="ROL-01",
            nombre="Administrador",
            descripcion="Administra usuarios, roles, sedes y catálogos del sistema",
            estado="activo",
            fecha_actualizacion=ahora(),
            responsable=settings.documento_admin_inicial,
            operaciones=list(sesion.scalars(select(modelos.OperacionModelo))),
        )
        sesion.add(administrador)
        sesion.flush()

    documento = settings.documento_admin_inicial
    hay_admin = sesion.scalar(select(modelos.UsuarioModelo).where(modelos.UsuarioModelo.documento == documento))
    if hay_admin is None and settings.contrasena_admin_inicial:
        sesion.add(modelos.UsuarioModelo(
            id_usuario="USR-0001",
            documento=documento,
            nombres="Administrador inicial",
            correo=settings.correo_admin_inicial,
            telefono="",
            id_sede=None,
            estado="activo",
            fecha_creacion=ahora(),
            responsable=documento,
        ))
        sesion.flush()
        sesion.add(modelos.CredencialModelo(
            documento=documento,
            hash_contrasena=generar_hash(settings.contrasena_admin_inicial),
            temporal=False,
            usada=False,
            id_rol=administrador.id_rol,
            fecha_actualizacion=ahora(),
        ))
    sesion.commit()
