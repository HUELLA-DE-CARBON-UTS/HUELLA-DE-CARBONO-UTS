"""Tablas de la base de datos.

MOD-01 Gestión de Usuarios: usuarios.
MOD-02 Gestión de Seguridad: operaciones, roles y credenciales.
MOD-03 Parametrización: sedes.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, UniqueConstraint
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
    # El administrador inicial no tiene sede; los demás usuarios siempre la tienen.
    id_sede: Mapped[str | None] = mapped_column(String(10), ForeignKey("sedes.id_sede"), nullable=True)
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))

    sede: Mapped[SedeModelo | None] = relationship(lazy="joined")


class CredencialModelo(Base):
    """Credencial de acceso y rol asignado de cada usuario (datos de MOD-02)."""

    __tablename__ = "credenciales"

    documento: Mapped[str] = mapped_column(String(15), ForeignKey("usuarios.documento"), primary_key=True)
    hash_contrasena: Mapped[str] = mapped_column(String(200))
    temporal: Mapped[bool] = mapped_column(Boolean, default=True)
    usada: Mapped[bool] = mapped_column(Boolean, default=False)
    id_rol: Mapped[str] = mapped_column(String(10), ForeignKey("roles.id_rol"))
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    rol: Mapped[RolModelo] = relationship(lazy="joined")
