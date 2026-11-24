from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.repositories.database.conexion import Base

rol_operacion = Table(
    "rol_operacion",
    Base.metadata,
    Column("id_rol", String(10), ForeignKey("roles.id_rol"), primary_key=True),
    Column("codigo_operacion", String(10), ForeignKey("operaciones.codigo"), primary_key=True),
)


class OperacionModelo(Base):
    __tablename__ = "operaciones"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))


class RolModelo(Base):
    __tablename__ = "roles"

    id_rol: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(200), default="")
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))

    operaciones: Mapped[list[OperacionModelo]] = relationship(secondary=rol_operacion, lazy="selectin")


class SedeModelo(Base):
    __tablename__ = "sedes"
    __table_args__ = (UniqueConstraint("nombre", "ciudad", name="uq_sede_nombre_ciudad"),)

    id_sede: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    ciudad: Mapped[str] = mapped_column(String(60))
    direccion: Mapped[str] = mapped_column(String(150))
    responsable: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(10), default="activa")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UsuarioModelo(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[str] = mapped_column(String(10), primary_key=True)
    documento: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    telefono: Mapped[str] = mapped_column(String(15), default="")
    id_sede: Mapped[str | None] = mapped_column(String(10), ForeignKey("sedes.id_sede"), nullable=True)
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))

    sede: Mapped[SedeModelo | None] = relationship(lazy="joined")


class CredencialModelo(Base):

    __tablename__ = "credenciales"

    documento: Mapped[str] = mapped_column(String(15), ForeignKey("usuarios.documento"), primary_key=True)
    hash_contrasena: Mapped[str] = mapped_column(String(200))
    temporal: Mapped[bool] = mapped_column(Boolean, default=True)
    usada: Mapped[bool] = mapped_column(Boolean, default=False)
    id_rol: Mapped[str] = mapped_column(String(10), ForeignKey("roles.id_rol"))
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    rol: Mapped[RolModelo] = relationship(lazy="joined")


class SesionModelo(Base):
    __tablename__ = "sesiones"

    id_sesion: Mapped[str] = mapped_column(String(10), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    documento: Mapped[str] = mapped_column(String(15), index=True)
    estado: Mapped[str] = mapped_column(String(12), default="vigente")
    requiere_cambio_contrasena: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_ingreso: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ultima_actividad: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_salida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventoBitacoraModelo(Base):
    __tablename__ = "bitacora_accesos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario: Mapped[str] = mapped_column(String(120), index=True)
    tipo_evento: Mapped[str] = mapped_column(String(30), index=True)
    operacion: Mapped[str] = mapped_column(String(10))
    id_sesion: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class HistorialCambioModelo(Base):
    __tablename__ = "historial_cambios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entidad: Mapped[str] = mapped_column(String(20))
    id_entidad: Mapped[str] = mapped_column(String(20), index=True)
    tipo_cambio: Mapped[str] = mapped_column(String(40))
    valor_anterior: Mapped[str] = mapped_column(String(400), default="")
    valor_nuevo: Mapped[str] = mapped_column(String(400), default="")
    motivo: Mapped[str] = mapped_column(String(300), default="")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))
