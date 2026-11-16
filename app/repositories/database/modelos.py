from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, UniqueConstraint
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
