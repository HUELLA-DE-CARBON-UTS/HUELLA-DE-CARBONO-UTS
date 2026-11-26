from dataclasses import dataclass
from datetime import date


@dataclass
class ElementoCatalogo:
    id: str
    nombre: str
    descripcion: str
    estado: str = "activo"


@dataclass
class Factor:
    valor: float
    vigente_desde: date
    vigente_hasta: date | None = None
    responsable: str = ""
    fuente: str | None = None
    id: int | None = None
