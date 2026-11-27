from dataclasses import dataclass
from datetime import datetime


@dataclass
class Usuario:
    id_usuario: str
    documento: str
    nombres: str
    correo: str
    telefono: str
    id_sede: str | None
    estado: str = "activo"
    fecha_creacion: datetime | None = None
