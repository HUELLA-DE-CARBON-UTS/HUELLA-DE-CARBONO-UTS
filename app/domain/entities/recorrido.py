from dataclasses import dataclass
from datetime import date


@dataclass
class Recorrido:
    codigo: str
    placa: str
    origen: str
    destino: str
    fecha_programada: date
    id_tipo: str
    id_combustible: str
    distancia_estimada_km: float | None = None
    estado: str = "programado"
    fecha_cierre: date | None = None
    distancia_km: float | None = None
    consumo_registrado_l: float | None = None
    motivo_cancelacion: str = ""


@dataclass
class ResultadoRecorrido:
    codigo: str
    distancia_km: float
    consumo_registrado_l: float
    estado_consumo: str = "pendiente"
    causa_consumo: str = ""
    id_factor_consumo: str | None = None
    factor_consumo_lkm: float | None = None
    consumo_estimado_l: float | None = None
    rendimiento_lkm: float | None = None
    desviacion_pct: float | None = None
    estado_emisiones: str = "pendiente"
    causa_emisiones: str = ""
    id_factor_emision: str | None = None
    factor_emision_kgco2l: float | None = None
    fuente_emision: str | None = None
    emisiones_kgco2: float | None = None
    version: int = 1

    def completo(self) -> bool:
        return self.estado_consumo == "completo" and self.estado_emisiones == "completo"
