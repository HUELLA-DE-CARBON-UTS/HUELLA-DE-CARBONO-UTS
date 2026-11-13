"""Entidad Rol del módulo MOD-02 Gestión de Seguridad."""

from dataclasses import dataclass, field


@dataclass
class Rol:
    id_rol: str
    nombre: str
    descripcion: str
    estado: str = "activo"
    permisos: list[str] = field(default_factory=list)
