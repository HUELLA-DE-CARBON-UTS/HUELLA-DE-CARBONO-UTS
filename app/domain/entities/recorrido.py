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
