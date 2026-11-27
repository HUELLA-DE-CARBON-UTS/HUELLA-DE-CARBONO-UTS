from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.database.conexion import Base


class VehiculoModelo(Base):
    __tablename__ = "vehiculos"

    placa: Mapped[str] = mapped_column(String(7), primary_key=True)
    id_sede: Mapped[str] = mapped_column(String(10), ForeignKey("sedes.id_sede"), index=True)
    estado: Mapped[str] = mapped_column(String(20), default="disponible")
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))


class FichaTecnicaModelo(Base):
    __tablename__ = "fichas_tecnicas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    placa: Mapped[str] = mapped_column(String(7), ForeignKey("vehiculos.placa"), index=True)
    id_tipo: Mapped[str] = mapped_column(String(10), ForeignKey("tipos_vehiculo.id_tipo"))
    id_combustible: Mapped[str] = mapped_column(String(10), ForeignKey("combustibles.id_combustible"))
    capacidad_t: Mapped[float] = mapped_column(Float)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsable: Mapped[str] = mapped_column(String(20))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True))
