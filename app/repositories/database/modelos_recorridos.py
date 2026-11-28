from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
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


class ResultadoRecorridoModelo(Base):
    __tablename__ = "resultados_recorridos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(12), ForeignKey("recorridos.codigo"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)
    distancia_km: Mapped[float] = mapped_column(Float)
    consumo_registrado_l: Mapped[float] = mapped_column(Float)
    estado_consumo: Mapped[str] = mapped_column(String(15))
    causa_consumo: Mapped[str] = mapped_column(String(200), default="")
    id_factor_consumo: Mapped[str | None] = mapped_column(String(12), nullable=True)
    factor_consumo_lkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    consumo_estimado_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    rendimiento_lkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    desviacion_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    estado_emisiones: Mapped[str] = mapped_column(String(15))
    causa_emisiones: Mapped[str] = mapped_column(String(200), default="")
    id_factor_emision: Mapped[str | None] = mapped_column(String(12), nullable=True)
    factor_emision_kgco2l: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuente_emision: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emisiones_kgco2: Mapped[float | None] = mapped_column(Float, nullable=True)
    fecha_calculo: Mapped[datetime] = mapped_column(DateTime(timezone=True))
