"""IC-01 verificarPermiso: decide si el rol de la sesión puede ejecutar una operación.

Versión inicial: valida contra los permisos guardados del rol. La
identificación de la sesión se completará con HU-06 (inicio de sesión) y
HU-07 (autorización de cada operación).
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.exceptions.errores import PermisoDenegado
from app.repositories.database.modelos import RolModelo


@dataclass
class SesionUsuario:
    documento: str
    rol: str


def verificar_permiso(db: Session, sesion: SesionUsuario, operacion: str, mensaje: str) -> None:
    rol = db.scalar(select(RolModelo).where(RolModelo.nombre == sesion.rol))
    autorizado = rol is not None and rol.estado == "activo" and any(o.codigo == operacion for o in rol.operaciones)
    if not autorizado:
        raise PermisoDenegado(mensaje, [{
            "campo": "sesion",
            "detalle": f"El rol {sesion.rol} no tiene autorizada la operación {operacion}",
        }])
