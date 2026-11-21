from dataclasses import dataclass
from datetime import datetime


@dataclass
class Sesion:
    id_sesion: str
    documento: str
    estado: str
    requiere_cambio_contrasena: bool
    fecha_ingreso: datetime
    ultima_actividad: datetime
    fecha_salida: datetime | None = None


@dataclass
class Credencial:
    documento: str
    hash_contrasena: str
    temporal: bool
    usada: bool
    id_rol: str
    nombre_rol: str
    estado_rol: str


@dataclass
class EventoBitacora:
    usuario: str
    tipo_evento: str
    operacion: str
    fecha: datetime
    id_sesion: str | None = None
