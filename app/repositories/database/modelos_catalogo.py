from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.database.conexion import Base


class TipoVehiculoModelo(Base):
    __tablename__ = "tipos_vehiculo"

    id_tipo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))


class FactorConsumoModelo(Base):
    __tablename__ = "factores_consumo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_tipo: Mapped[str] = mapped_column(String(10), ForeignKey("tipos_vehiculo.id_tipo"), index=True)
    valor: Mapped[float] = mapped_column(Float)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsable: Mapped[str] = mapped_column(String(20))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CombustibleModelo(Base):
    __tablename__ = "combustibles"

    id_combustible: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))


class FactorEmisionModelo(Base):
    __tablename__ = "factores_emision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_combustible: Mapped[str] = mapped_column(String(10), ForeignKey("combustibles.id_combustible"), index=True)
    valor: Mapped[float] = mapped_column(Float)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    fuente: Mapped[str] = mapped_column(String(200))
    responsable: Mapped[str] = mapped_column(String(20))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True))
