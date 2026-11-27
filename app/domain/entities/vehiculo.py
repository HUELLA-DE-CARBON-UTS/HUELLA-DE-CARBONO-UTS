from dataclasses import dataclass
from datetime import date


@dataclass
class Vehiculo:
    placa: str
    id_sede: str
    estado: str = "disponible"


@dataclass
class FichaTecnica:
    id_tipo: str
    id_combustible: str
    capacidad_t: float
    vigente_desde: date
    vigente_hasta: date | None = None
    responsable: str = ""
    id: int | None = None

    def aplica_en(self, dia: date) -> bool:
        return self.vigente_desde <= dia and (self.vigente_hasta is None or dia <= self.vigente_hasta)
