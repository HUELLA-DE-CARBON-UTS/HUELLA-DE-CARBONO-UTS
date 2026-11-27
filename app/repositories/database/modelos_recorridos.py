from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.database.conexion import Base


class RecorridoModelo(Base):
    __tablename__ = "recorridos"

    codigo: Mapped[str] = mapped_column(String(12), primary_key=True)
    placa: Mapped[str] = mapped_column(String(7), ForeignKey("vehiculos.placa"), index=True)
    origen: Mapped[str] = mapped_column(String(120))
    destino: Mapped[str] = mapped_column(String(120))
    fecha_programada: Mapped[date] = mapped_column(Date)
    distancia_estimada_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    id_tipo: Mapped[str] = mapped_column(String(10))
    id_combustible: Mapped[str] = mapped_column(String(10))
    estado: Mapped[str] = mapped_column(String(15), default="programado", index=True)
    fecha_cierre: Mapped[date | None] = mapped_column(Date, nullable=True)
    distancia_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    consumo_registrado_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    motivo_cancelacion: Mapped[str] = mapped_column(String(300), default="")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responsable: Mapped[str] = mapped_column(String(20))
