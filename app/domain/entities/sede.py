"""Entidad Sede del módulo MOD-03 Parametrización."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Sede:
    id_sede: str
    nombre: str
    ciudad: str
    direccion: str
    responsable: str
    estado: str = "activa"
    fecha_creacion: datetime | None = None
